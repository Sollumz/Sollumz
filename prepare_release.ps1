param(
  # The new version
  [Parameter(Mandatory=$true)]
  [string]
  $Version
)

if ((Get-Command "git" -ErrorAction SilentlyContinue) -eq $null)
{
  Throw "'git' not available in PATH!"
}

# Gets the szio version pinned in dependencies.py at the given revision, or $null if there is none
function Get-SzioVersion([string]$Rev) {
  $deps = (& git show "${Rev}:dependencies.py" 2>$null) -join "`n"
  if ($deps -match '(?s)Dependency\(\s*"szio",.*?"(\d+\.\d+\.\d+(?:\.dev\d+)?)"') {
    return $Matches[1]
  }
  return $null
}

$Version = $Version.TrimStart("v")

$versionComponents = $Version.Split(".") -match "^\d+$"
if ($versionComponents.Length -ne 3) {
  Throw "Version expected to have 3 numbers!"
}

$major = $versionComponents[0]
$minor = $versionComponents[1]
$patch = $versionComponents[2]

# Remember the commit before the release changes, to tell how to revert them
$originalHead = & git rev-parse --short HEAD

# Update version in __init__.py
(Get-Content -Raw __init__.py) `
  -replace "`"version`": \(\d+, \d+, \d+\)", "`"version`": ($major, $minor, $patch)" |
Set-Content -NoNewline __init__.py

# Update version in blender_manifest.toml and set the extension ID used for releases
(Get-Content -Raw blender_manifest.toml) `
  -replace "`nversion = .*", "`nversion = `"$major.$minor.$patch`"" `
  -replace "`nid = .*",      "`nid = `"sollumz`"" `
  -replace "`nname = .*",    "`nname = `"Sollumz`"" |
Set-Content -NoNewline blender_manifest.toml


# Create commit and tag as a release
& git add __init__.py blender_manifest.toml
& git commit -m "chore: prepare release v$Version"
& git tag -a -m "Release v$Version" "v$Version"

Write-Host "Add-on version updated and commited. When ready, push with ``git push --follow-tags``"


# Generate release notes from commit messages with git-cliff
if ((Get-Command "git-cliff" -ErrorAction SilentlyContinue) -eq $null)
{
  Write-Warning "Cannot find 'git-cliff' in PATH. Release notes won't be generated. If desired, install with 'cargo install --git https://github.com/orhun/git-cliff'."
}
else
{
  & git-cliff --current -c cliff.toml -o RELEASE_NOTES.md

  # Append the szio changes between the versions pinned by the previous release and this one
  $prevTag = & git describe --tags --abbrev=0 --match "v[0-9]*" "v$Version^"
  $szioOld = Get-SzioVersion $prevTag
  $szioNew = Get-SzioVersion "v$Version"
  if ($szioOld -and $szioNew -and $szioOld -ne $szioNew)
  {
    # git-cliff needs a local repo, use a throwaway clone with only the commit history
    $szioRepo = Join-Path ([IO.Path]::GetTempPath()) "szio-$([guid]::NewGuid()).git"
    & git clone --quiet --bare --filter=blob:none https://github.com/Sollumz/szio.git $szioRepo
    $szioNotes = Join-Path $szioRepo "RELEASE_NOTES.md"

    # Only the two pinned versions count as tags, so the whole range ends up in a single section
    $szioTags = "^v($([regex]::Escape($szioOld))|$([regex]::Escape($szioNew)))$"
    & git-cliff -c cliff.toml -r $szioRepo --github-repo Sollumz/szio --tag-pattern $szioTags --strip all -o $szioNotes "v$szioOld..v$szioNew"
    Add-Content -Encoding UTF8 -Path RELEASE_NOTES.md -Value ("`n" + (Get-Content -Raw -Encoding UTF8 $szioNotes))

    Remove-Item -Recurse -Force $szioRepo
  }
  Write-Host "Release notes written to 'RELEASE_NOTES.md'. Might need some clean up before publishing the GitHub release."
}


# Add the commit placeholder and dev extension ID back to differentiate development commits from the release
(Get-Content -Raw blender_manifest.toml) `
  -replace "`nversion = .*", "`nversion = `"$major.$minor.$patch-dev+`$Format:%h`$`"" `
  -replace "`nid = .*",      "`nid = `"sollumz_dev`"" `
  -replace "`nname = .*",    "`nname = `"Sollumz (Development)`"" |
Set-Content -NoNewline blender_manifest.toml


& git add blender_manifest.toml
& git commit -m "chore: prepare development manifest"


# Create archive
& git archive --prefix Sollumz/ -o Sollumz.zip "v$Version"
Write-Host "Archive created in 'Sollumz.zip'."

Write-Host "To revert the git changes, run ``git tag -d v$Version`` and ``git reset --keep $originalHead``"
