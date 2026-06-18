$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$versionFile = Join-Path $root 'packaging\version.json'
if (-not (Test-Path $versionFile)) {
    throw "Missing packaging\\version.json."
}

$versionMeta = Get-Content $versionFile -Raw | ConvertFrom-Json

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required to build the installer."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is required to build the frontend."
}

if (-not (Get-Command iscc -ErrorAction SilentlyContinue)) {
    throw "Inno Setup Compiler (iscc) is required to build the installer."
}

Write-Host "Generating application icon..."
python packaging\generate_icon.py

Write-Host "Generating version metadata..."
python packaging\generate_version_info.py

Write-Host "Building frontend..."
Push-Location frontend
try {
    npm ci
    npm run build
} finally {
    Pop-Location
}

Write-Host "Building bundled application..."
python -m PyInstaller Iconique.spec --noconfirm --clean

Write-Host "Building Windows installer..."
$defines = @(
    "/DMyAppName=$($versionMeta.app_name)",
    "/DMyAppVersion=$($versionMeta.version)",
    "/DMyAppPublisher=$($versionMeta.publisher)",
    "/DMyAppPublisherURL=$($versionMeta.publisher_url)",
    "/DMyAppSupportURL=$($versionMeta.support_url)",
    "/DMyAppUpdatesURL=$($versionMeta.updates_url)"
)
& iscc @defines packaging\iconique.iss

Write-Host "Installer finished. Check packaging\installer-output\ for the setup EXE."
