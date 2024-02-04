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
(Get-Content -Raw __init__.py) -replace "`"version`": \(\d+, \d+, \d+\)", "`"version`": ($major, $minor, $patch)" |
Set-Content -NoNewline __init__.py

# Create commit and tag
& git add __init__.py
& git commit -m "chore: bump version to $Version"
& git tag "v$Version"

Write-Host "Add-on version updated and commited. When ready, push with ``git push && git push --tags``"

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

# Create archive
& git archive --prefix Sollumz/ -o Sollumz.zip "v$Version"
Write-Host "Archive created in 'Sollumz.zip'."
