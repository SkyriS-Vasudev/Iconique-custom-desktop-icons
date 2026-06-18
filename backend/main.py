import os
import sys
import socket
import threading
import shutil
import json
from urllib.parse import quote
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

try:
    import webview
except ImportError:  # pragma: no cover - optional runtime dependency
    webview = None

from backend.logging_config import logger
from backend.database import (
    init_db, get_setting, set_setting, get_history, 
    add_history_entry, get_all_backups
)
from backend.icon_converter import convert_to_ico, generate_preview, get_assets_dir
from backend.icon_manager import (
    discover_shortcuts, apply_custom_icon, restore_shortcut_icon, 
    restore_all_shortcuts, create_desktop_shortcut_and_modify,
    get_cache_dir, get_backups_dir
)

# Initialize database
init_db()

app = FastAPI(title="Iconique API", version="1.0.0")

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get theme packs directory
def get_theme_packs_dir():
    # 1. Check AppData
    appdata = os.getenv('APPDATA')
    base_dir = get_resource_root()
    local_themes = os.path.join(base_dir, 'Theme Packs')
    appdata_themes = None

    if appdata:
        candidate = os.path.join(appdata, 'Iconique', 'Theme Packs')
        try:
            os.makedirs(candidate, exist_ok=True)
            appdata_themes = candidate
        except OSError:
            logger.warning("AppData theme directory is not writable; falling back to workspace themes.")

    # 2. Check local workspace
    return local_themes, appdata_themes


def get_resource_root():
    """
    Resolve the base directory for bundled resources.

    When packaged with PyInstaller, resources live under sys._MEIPASS. During
    source development, they live at the repo root.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMMON_APP_CANDIDATES = [
    {
        "name": "Google Chrome",
        "paths": [
            r"Google\Chrome\Application\chrome.exe",
            r"Google\Chrome\Application\chrome_proxy.exe",
        ],
    },
    {
        "name": "Microsoft Edge",
        "paths": [
            r"Microsoft\Edge\Application\msedge.exe",
        ],
    },
    {
        "name": "Visual Studio Code",
        "paths": [
            r"Microsoft VS Code\Code.exe",
            r"Programs\Microsoft VS Code\Code.exe",
        ],
    },
    {
        "name": "Git Bash",
        "paths": [
            r"Git\git-bash.exe",
            r"Git\bin\bash.exe",
        ],
    },
    {
        "name": "Notepad++",
        "paths": [
            r"Notepad++\notepad++.exe",
        ],
    },
]


def _program_files_roots():
    roots = []
    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = os.getenv(key)
        if value:
            roots.append(value)
    return roots


def scan_common_executables():
    discovered = []
    seen_paths = set()

    for candidate in COMMON_APP_CANDIDATES:
        for root in _program_files_roots():
            for rel_path in candidate["paths"]:
                exe_path = os.path.join(root, rel_path)
                if exe_path in seen_paths:
                    continue
                if os.path.exists(exe_path):
                    seen_paths.add(exe_path)
                    discovered.append({
                        "name": candidate["name"],
                        "path": exe_path.replace('\\', '/'),
                    })

    return discovered

# API Routes
@app.get("/api/shortcuts")
def get_shortcuts():
    try:
        shortcuts = discover_shortcuts()
        return shortcuts
    except Exception as e:
        logger.error(f"Error getting shortcuts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
def upload_image(file: UploadFile = File(...)):
    try:
        # Create temp folder for upload
        temp_dir = os.path.join(get_assets_dir(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Convert to ICO
        ico_name = f"custom_{os.path.splitext(file.filename)[0]}"
        ico_path = convert_to_ico(temp_path, output_name=ico_name)
        
        # Generate PNG preview
        preview_path = generate_preview(temp_path, output_name=ico_name)
        
        # Clean up temp upload file
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Could not delete temp upload file: {e}")
            
        return {
            "success": True,
            "icoPath": ico_path.replace('\\', '/'),
            "previewPath": f"/api/assets/custom/{os.path.basename(preview_path)}"
        }
    except Exception as e:
        logger.error(f"Upload and conversion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/shortcuts/apply")
def apply_shortcut_icon(
    shortcut_path: str = Form(...), 
    ico_path: str = Form(...), 
    action_type: str = Form("applied_custom")
):
    try:
        success, msg = apply_custom_icon(shortcut_path, ico_path, action_type)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Apply icon failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shortcuts/restore")
def restore_shortcut(shortcut_path: str = Form(...)):
    try:
        success, msg = restore_shortcut_icon(shortcut_path)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Restore icon failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shortcuts/restore-all")
def restore_all():
    try:
        success, msg = restore_all_shortcuts()
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Restore all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shortcuts/create-shortcut")
def create_shortcut(
    exe_path: str = Form(...), 
    app_name: str = Form(...), 
    ico_path: str = Form(...)
):
    try:
        success, msg = create_desktop_shortcut_and_modify(exe_path, app_name, ico_path)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Create shortcut failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/themes")
def get_themes():
    local_themes, appdata_themes = get_theme_packs_dir()
    themes = []
    
    # Scan both theme directories
    for directory in [path for path in [local_themes, appdata_themes] if path]:
        if not os.path.exists(directory):
            continue
            
        for folder_name in os.listdir(directory):
            folder_path = os.path.join(directory, folder_name)
            if not os.path.isdir(folder_path):
                continue
                
            theme_json_path = os.path.join(folder_path, "theme.json")
            try:
                meta = {}
                if os.path.exists(theme_json_path):
                    with open(theme_json_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)

                resolved_icons = {}
                icon_entries = []

                if meta.get("icons"):
                    for app_name, icon_filename in meta.get("icons", {}).items():
                        icon_path = os.path.join(folder_path, icon_filename)
                        if os.path.exists(icon_path):
                            icon_data = {
                                "path": icon_path.replace('\\', '/'),
                                "url": f"/api/assets/theme/{quote(folder_name)}/{quote(icon_filename)}",
                                "label": app_name,
                                "filename": icon_filename,
                            }
                            resolved_icons[app_name] = icon_data
                            icon_entries.append(icon_data)
                else:
                    for icon_filename in sorted(os.listdir(folder_path)):
                        if not icon_filename.lower().endswith(".ico"):
                            continue
                        icon_path = os.path.join(folder_path, icon_filename)
                        label = os.path.splitext(icon_filename)[0].replace('_', ' ').replace('-', ' ')
                        icon_entries.append({
                            "path": icon_path.replace('\\', '/'),
                            "url": f"/api/assets/theme/{quote(folder_name)}/{quote(icon_filename)}",
                            "label": label,
                            "filename": icon_filename,
                        })

                if not resolved_icons and icon_entries:
                    for entry in icon_entries:
                        resolved_icons[entry["label"]] = entry

                if resolved_icons or icon_entries:
                    theme_data = {
                        "id": folder_name,
                        "name": meta.get("name", folder_name),
                        "author": meta.get("author", "Local Pack"),
                        "description": meta.get("description", "Custom icon pack discovered from this theme folder."),
                        "category": meta.get("category", "Custom"),
                        "icons": resolved_icons,
                        "iconEntries": icon_entries,
                    }
                    themes.append(theme_data)
            except Exception as e:
                logger.error(f"Failed to parse theme folder {folder_name}: {e}")
                    
    return themes

@app.get("/api/assets/theme/{theme_name}/{filename}")
def get_theme_asset(theme_name: str, filename: str):
    local_themes, appdata_themes = get_theme_packs_dir()
    for root in [path for path in (local_themes, appdata_themes) if path]:
        path = os.path.join(root, theme_name, filename)
        if os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="Theme asset not found.")

@app.get("/api/history")
def get_activity_history():
    try:
        return get_history(limit=100)
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def get_app_settings():
    return {
        "themeMode": get_setting("themeMode", "dark"),
        "filterType": get_setting("filterType", "all"),
        "backupLocation": get_setting("backupLocation", "appdata"),
        "autoScanCommonApps": get_setting("autoScanCommonApps", "false"),
    }

@app.post("/api/settings")
def save_app_settings(
    themeMode: str = Form(None),
    filterType: str = Form(None),
    backupLocation: str = Form(None),
    autoScanCommonApps: str = Form(None),
):
    if themeMode:
        set_setting("themeMode", themeMode)
    if filterType:
        set_setting("filterType", filterType)
    if backupLocation in {"appdata", "workspace"}:
        set_setting("backupLocation", backupLocation)
    if autoScanCommonApps is not None:
        set_setting("autoScanCommonApps", autoScanCommonApps.lower() in {"1", "true", "yes", "on"})
    return {"success": True}

@app.get("/api/apps/common")
def get_common_apps():
    auto_scan_enabled = get_setting("autoScanCommonApps", "false").lower() in {"1", "true", "yes", "on"}
    if not auto_scan_enabled:
        return {"enabled": False, "apps": []}

    return {
        "enabled": True,
        "apps": scan_common_executables(),
    }


class DesktopBridge:
    def pick_executable(self):
        try:
            if not webview.windows:
                return None

            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG)
            if not result:
                return None

            if isinstance(result, (list, tuple)):
                return result[0]
            return result
        except Exception as exc:
            logger.warning(f"Executable picker failed: {exc}")
            return None

# Serve Dynamic Asset Files (Cached Icons, Custom Previews, Theme Icons)
@app.get("/api/assets/cache/{filename}")
def get_cached_icon(filename: str):
    path = os.path.join(get_cache_dir(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Cached icon not found.")

@app.get("/api/assets/backup/{filename}")
def get_backup_icon(filename: str):
    path = os.path.join(get_backups_dir(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Backup icon not found.")

@app.get("/api/assets/custom/{filename}")
def get_custom_asset(filename: str):
    path = os.path.join(get_assets_dir(), filename)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Asset file not found.")

# Serve static frontend files in production
frontend_dir = os.path.join(get_resource_root(), "frontend", "dist")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Serving built React frontend from: {frontend_dir}")
else:
    logger.warning(f"Built frontend directory not found at {frontend_dir}. Running in API-only fallback mode.")

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_fastapi(port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

def main():
    logger.info("Starting Iconique desktop application...")

    if webview is None:
        logger.error("PyWebView is not installed. Install the desktop runtime dependencies to launch Iconique.")
        return
    
    # 1. Find free port and start FastAPI in background thread
    port = find_free_port()
    api_url = f"http://127.0.0.1:{port}"
    logger.info(f"FastAPI starting on {api_url}")
    
    t = threading.Thread(target=run_fastapi, args=(port,))
    t.daemon = True
    t.start()
    
    # Check if running in dev mode or prod mode
    # If dev mode, we redirect to Vite development server (localhost:5173) if active
    url_to_load = api_url
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        url_to_load = f"http://localhost:5173/?api={quote(api_url, safe='')}"
        logger.info(f"Dev mode active: loading frontend from {url_to_load}")
    
    # 2. Launch PyWebView Window
    try:
        # We can use standard styling.
        # WebView2 (system Edge) will load our React app.
        webview.create_window(
            title="Iconique",
            url=url_to_load,
            width=1100,
            height=750,
            min_size=(900, 600),
            background_color="#121214",
            js_api=DesktopBridge(),
        )
        webview.start()
    except Exception as e:
        logger.error(f"PyWebView failed to start: {e}")
        print(f"Error starting desktop window: {e}. Please ensure WebView2 Runtime is installed.")

if __name__ == "__main__":
    # If uvicorn runs this script as a subprocess (e.g. reload), do not spawn webview
    if "uvicorn" not in sys.argv[0]:
        main()
