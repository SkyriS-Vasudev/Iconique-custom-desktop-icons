# Iconique

Iconique is a lightweight Windows desktop personalization tool that allows users to customize desktop shortcut icons, generate icons from images, apply curated theme packs, and restore original icons from backups.

The application combines a modern desktop interface with local Windows integration, enabling seamless icon customization without requiring users to manually edit shortcuts or convert image formats.

---

## Features

### Desktop Shortcut Management

- Automatically discovers desktop shortcuts
- Displays installed shortcuts in a visual interface
- Supports icon customization for Windows shortcut files (`.lnk`)

### Custom Icons

- Upload your own images
- Drag and drop image support
- Automatic image validation
- Automatic conversion to Windows `.ico` format
- Live icon previews before applying

### Theme Packs

Included theme packs:

- Pokémon Theme
- Legally Blonde Theme
- HP Theme

Theme packs can be expanded by adding new pack folders.

### Backup & Restore

- Automatic backup before icon changes
- Restore original icon for individual shortcuts
- Restore all customized shortcuts
- Persistent backup storage

### Activity Tracking

- Change history
- Backup records
- Application logs

---

## Requirements

### Runtime

- Windows 10 or Windows 11
- Python 3.10+
- Node.js 18+
- Microsoft Edge WebView2 Runtime

Most modern Windows installations already include WebView2.

---

## Run From Source

### 1. Clone the Repository

```powershell
git clone https://github.com/<your-username>/iconique.git
cd iconique
```

### 2. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```powershell
cd frontend
npm ci
```

### 4. Build Frontend Assets

```powershell
npm run build
```

### 5. Return to Project Root

```powershell
cd ..
```

### 6. Launch the Application

```powershell
python -m backend.main
```

---

## Project Structure

```text
Iconique/
│
├── backend/
│
├── frontend/
│
├── packaging/
│
├── Theme Packs/
│   ├── pokemon theme/
│   ├── legally blonde theme/
│   └── hp theme/
│
├── requirements.txt
├── README.md
└── Iconique.spec
```

---

## Theme Packs

Theme packs are stored in:

```text
Theme Packs/
```

Each theme pack contains its own icons and metadata.

Example:

```text
Theme Packs/
└── pokemon theme/
    ├── icons/
    └── metadata.json
```

New theme packs can be added without modifying application code.

---

## Data Storage

Application data is stored in:

```text
%APPDATA%\Iconique\
```

This includes:

- User settings
- Backup data
- Custom icons
- History records

If Windows profile storage is unavailable, the application falls back to local workspace storage.

---

## Build The Installer

### Prerequisites

Install:

- Python 3
- Node.js
- Inno Setup Compiler

### Build

Run:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
```

### Output

Generated installers are placed in:

```text
packaging\installer-output\
```

---

## Versioning

Application and installer metadata are controlled from:

```text
packaging/version.json
```

Update this file before creating a release.

Example:

```json
{
  "version": "1.0.0",
  "company": "Iconique",
  "product_name": "Iconique"
}
```

---

## Installer Features

The generated installer:

- Installs the application under Program Files
- Creates Start Menu shortcuts
- Optionally creates a Desktop shortcut
- Bundles frontend assets
- Bundles backend code
- Bundles theme packs
- Applies version metadata automatically

---

## WebView2 Runtime

Iconique uses PyWebView for its desktop interface.

PyWebView requires Microsoft Edge WebView2.

Most Windows 11 systems already include it.

If WebView2 is missing, install the Microsoft Edge WebView2 Runtime before launching the application.

---

## Troubleshooting

### ModuleNotFoundError: No module named 'backend'

Launch the application using:

```powershell
python -m backend.main
```

instead of:

```powershell
python backend\main.py
```

### Frontend Not Updating

Rebuild the frontend:

```powershell
cd frontend
npm run build
```

### Installer Build Fails

Verify:

- Python is installed
- Node.js is installed
- Inno Setup Compiler is installed
- All dependencies from `requirements.txt` are installed

---

## Development Checklist

Before publishing a release:

- [ ] Application launches successfully
- [ ] Frontend builds without errors
- [ ] Desktop shortcuts are discovered
- [ ] Custom icon upload works
- [ ] Theme packs load correctly
- [ ] Restore functionality works
- [ ] Installer builds successfully
- [ ] Installer installs successfully on a clean machine
- [ ] No hardcoded local file paths remain
- [ ] README is up to date

---

## License

This project is provided for educational and personal use.