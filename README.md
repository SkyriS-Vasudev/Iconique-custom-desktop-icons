<div align="center">

# ✨ Iconique

**A premium Windows desktop icon customizer**

Transform your boring desktop shortcuts into beautiful, themed icons — no manual editing, no format headaches.

![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?style=flat-square&logo=windows&logoColor=white)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-Personal%20%26%20Educational-green?style=flat-square)

---

</div>

## 🎯 What is Iconique?

Iconique is a sleek, modern desktop application for **Windows 10 & 11** that lets you customize your desktop shortcut icons in seconds. It wraps a polished React interface around native Windows shell integration so you can:

- **Browse curated theme packs** and apply matching icons to your desktop shortcuts
- **Upload any image** (PNG, JPG, SVG, WebP) and it auto-converts to `.ico` format
- **Create new desktop shortcuts** from your installed apps library — with a custom icon applied instantly
- **Restore original icons** any time with one click, thanks to automatic backups

No registry hacking. No right-click → Properties → Change Icon. Just pick, preview, and apply.

---

## 🖼️ Features

### 🎨 Theme Packs
Pre-built icon packs ship with the app. Each pack contains a curated set of `.ico` files designed around a specific aesthetic:

| Pack | Style |
|------|-------|
| **Pokémon** | Iconic Pokémon characters as app icons |
| **Legally Blonde** | Pink-themed, playful icons |
| **HP** | Harry Potter-inspired wizarding icons |
| **Cyberpunk** | Neon-edged, futuristic icons |

You can also create your own packs — just drop a folder with `.ico` files and a `theme.json` into the `Theme Packs/` directory.

### 🔄 Automatic Backup & Restore
Every time you change an icon, Iconique saves the original configuration. You can restore a single shortcut or bulk-restore everything back to defaults.

### 📤 Custom Icon Upload
Upload any image file and Iconique will:
1. Validate the image
2. Convert it to a multi-resolution `.ico` file
3. Save it permanently so Windows never loses your icon
4. Show you a live preview before applying

### 🖥️ Create Desktop Shortcuts
Don't have a desktop shortcut for an app? Iconique scans your Start Menu for all installed applications and lets you create a shortcut with one click. It automatically extracts the app's native icon — or lets you pick a theme icon instead.

### 🌗 Light & Dark Mode
Switch between light and dark themes from the sidebar. Both modes are designed for high contrast and readability.

---

## 📦 Installation

### Option A: Run the Installer (Recommended)

1. Download `IconiqueSetup-1.0.0.exe` from the [Releases](https://github.com/SkyriS-Vasudev/Iconique-custom-desktop-icons/releases) page.
   OR
  Clone the repository to your local machine.
2. Navigate to the Installers Folder and click on IconiqueSetup-1.0.0
3. Run the installer — it will guide you through setup
4. Launch **Iconique** from your Start Menu or Desktop

> [!NOTE]
> The installer bundles everything (Python runtime, frontend, theme packs). No additional software is required.

### Option B: Run from Source

#### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (pre-installed on most Windows 11 systems)

#### Steps

```powershell
# 1. Clone the repository
git clone https://github.com/SkyriS-Vasudev/Iconique-custom-desktop-icons.git
cd Iconique-custom-desktop-icons

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install and build the frontend
cd frontend
npm ci
npm run build
cd ..

# 5. Launch the application
python -m backend.main
```

The app window should open automatically. If it doesn't, check the terminal output for the local URL (usually `http://localhost:8000`).

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, Vite 8, Vanilla CSS | UI, theming, icon browsing |
| **Icons** | Lucide React | UI iconography |
| **Backend** | Python, FastAPI, Uvicorn | REST API, file operations, shell integration |
| **Image Processing** | Pillow (PIL) | Image validation, ICO conversion, previews |
| **Desktop Shell** | PyWebView + Edge WebView2 | Native window, file dialogs |
| **Windows Integration** | PowerShell, .NET System.Drawing | Shortcut manipulation, icon extraction, explorer refresh |
| **Database** | SQLite | Backup records, user settings |
| **Packaging** | PyInstaller + Inno Setup | Bundled exe + Windows installer |

---

## 📁 Project Structure

```
Iconique/
├── backend/                    # Python FastAPI server
│   ├── main.py                 # API routes & app entry point
│   ├── icon_manager.py         # Shortcut discovery, icon apply/restore
│   ├── icon_converter.py       # Image → ICO conversion logic
│   ├── database.py             # SQLite backup & settings storage
│   ├── logging_config.py       # Logging setup
│   └── schema.sql              # Database schema
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx             # Main application component
│   │   ├── App.css             # Core styles & layout
│   │   └── styles/
│   │       └── variables.css   # CSS custom properties & theming
│   └── package.json
│
├── Theme Packs/                # Curated icon theme packs
│   ├── Pokemon/
│   ├── Legally Blonde/
│   ├── HP/
│   ├── Cyberpunk/
│   └── Custom/                 # User-created icons go here
│
├── packaging/                  # Build & installer tooling
│   ├── build_installer.ps1     # One-script full build pipeline
│   ├── iconique.iss            # Inno Setup installer script
│   ├── generate_icon.py        # App icon generator
│   ├── generate_version_info.py
│   └── version.json            # Version metadata
│
├── Installers/                 # Built installer output
├── Iconique.spec               # PyInstaller bundling config
└── requirements.txt            # Python dependencies
```

---

## 🏗️ Building the Installer

To build a distributable Windows installer from source:

#### Prerequisites
- Python 3.10+
- Node.js 18+
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (free)

#### Build

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
```

This single script will:
1. Generate the application icon
2. Generate version metadata
3. Build the React frontend (`npm ci && npm run build`)
4. Bundle everything with PyInstaller
5. Compile the Windows installer with Inno Setup

The output installer will be at: `Installers/IconiqueSetup-1.0.0.exe`

---

## 💾 Data Storage

All user data is stored in:
```
%APPDATA%\Iconique\
├── cache/          # Extracted icon previews (PNG)
├── backups/        # Original icon backups
├── assets/         # Converted custom icons (ICO)
├── Theme Packs/    # User-added theme packs (synced at runtime)
└── iconique.db     # SQLite database (settings, backup records)
```

If `%APPDATA%` is unavailable, the app falls back to local workspace storage.

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'backend'` | Run with `python -m backend.main` instead of `python backend\main.py` |
| Frontend not updating after code changes | Rebuild: `cd frontend && npm run build` |
| Icons not refreshing on desktop | Iconique calls `SHChangeNotify` automatically, but you can also press **F5** on your desktop |
| Installer build fails | Ensure Python, Node.js, and Inno Setup 6 are all installed and on your PATH |
| WebView2 error on launch | Install the [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-theme`)
3. Make your changes
4. Test locally (run from source, verify the installer builds)
5. Submit a Pull Request

### Adding a Theme Pack

1. Create a new folder under `Theme Packs/` (e.g., `Theme Packs/My Theme/`)
2. Add `.ico` files (256×256 recommended)
3. Optionally add a `theme.json` with metadata:
   ```json
   {
     "name": "My Theme",
     "author": "Your Name",
     "description": "A short description of your theme",
     "category": "Custom",
     "icons": {
       "Google Chrome": "chrome.ico",
       "Visual Studio Code": "vscode.ico"
     }
   }
   ```
4. Restart Iconique — the new pack appears automatically

---

## 📋 License

This project is provided for **educational and personal use**.

---

<div align="center">

Made with ❤️ for desktop aesthetics

</div>
