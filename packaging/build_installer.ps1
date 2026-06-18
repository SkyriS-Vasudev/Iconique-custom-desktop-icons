$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$versionFile = Join-Path $root 'packaging\version.json'
if (-not (Test-Path $versionFile)) {
    throw "Missing packaging\\version.json."
}

$versionMeta = Get-Content $versionFile -Raw | ConvertFrom-Json

# Resolve Python path (prefer virtual environment)
$pythonPath = "python"
if (Test-Path ".venv") {
    $pythonPath = ".venv\Scripts\python.exe"
    Write-Host "Using virtual environment Python at: $pythonPath"
} else {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python is required to build the installer."
    }
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is required to build the frontend."
}

# Resolve Inno Setup Compiler path
$isccPath = "iscc"
if (-not (Get-Command iscc -ErrorAction SilentlyContinue)) {
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\iscc.exe",
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) {
            $isccPath = $p
            break
        }
    }
}

if ($isccPath -eq "iscc" -and -not (Get-Command iscc -ErrorAction SilentlyContinue)) {
    throw "Inno Setup Compiler (iscc) is required to build the installer."
}
Write-Host "Using Inno Setup compiler path: $isccPath"

Write-Host "Generating application icon..."
& $pythonPath packaging\generate_icon.py

Write-Host "Generating version metadata..."
& $pythonPath packaging\generate_version_info.py

Write-Host "Building frontend..."
Push-Location frontend
try {
    npm ci
    npm run build
} finally {
    Pop-Location
}

Write-Host "Building bundled application..."
& $pythonPath -m PyInstaller Iconique.spec --noconfirm --clean

Write-Host "Building Windows installer..."
$defines = @(
    "/DMyAppName=$($versionMeta.app_name)",
    "/DMyAppVersion=$($versionMeta.version)",
    "/DMyAppPublisher=$($versionMeta.publisher)",
    "/DMyAppPublisherURL=$($versionMeta.publisher_url)",
    "/DMyAppSupportURL=$($versionMeta.support_url)",
    "/DMyAppUpdatesURL=$($versionMeta.updates_url)"
)
& $isccPath @defines packaging\iconique.iss

Write-Host "Installer finished. Check packaging\installer-output\ for the setup EXE."

