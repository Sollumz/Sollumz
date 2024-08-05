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

$Version = $Version.TrimStart("v")

$versionComponents = $Version.Split(".") -match "^\d+$"
if ($versionComponents.Length -ne 3) {
  Throw "Version expected to have 3 numbers!"
}

$major = $versionComponents[0]
$minor = $versionComponents[1]
$patch = $versionComponents[2]

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
