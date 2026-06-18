# Iconique

Iconique is a lightweight Windows desktop personalization tool for applying custom icons to desktop shortcuts, creating new shortcut icons from EXE files, and restoring originals from backups.

## Run From Source

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Build the frontend once:
   ```powershell
   cd frontend
   npm ci
   npm run build
   ```

3. Launch the desktop app:
   ```powershell
   python backend\main.py
   ```

## Build The Installer

This repo now includes a Windows installer pipeline based on PyInstaller + Inno Setup.

1. Install the build tools:
   - Python 3
   - Node.js
   - Inno Setup Compiler

2. Build the app and installer:
   ```powershell
   powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
   ```

3. Find the installer in:
   ```text
   packaging\installer-output\
   ```

## What The Installer Does

- Installs the app under `Program Files`
- Creates Start Menu shortcuts
- Optionally creates a desktop shortcut
- Bundles the React frontend, backend, and theme packs into the app

## Notes

- Backup data and app settings are stored in `%APPDATA%\Iconique\` by default.
- The app falls back to workspace-local storage when Windows profile storage is not writable.
