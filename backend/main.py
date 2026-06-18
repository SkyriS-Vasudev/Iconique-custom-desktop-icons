import os
import sys
import socket
import threading
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import webview

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
    if not appdata:
        appdata = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    appdata_themes = os.path.join(appdata, 'Iconique', 'Theme Packs')
    
    # Create it if it doesn't exist so users can drop packs there
    os.makedirs(appdata_themes, exist_ok=True)
    
    # 2. Check local workspace
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_themes = os.path.join(base_dir, 'Theme Packs')
    
    return local_themes, appdata_themes

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
    for directory in [local_themes, appdata_themes]:
        if not os.path.exists(directory):
            continue
            
        for folder_name in os.listdir(directory):
            folder_path = os.path.join(directory, folder_name)
            if not os.path.isdir(folder_path):
                continue
                
            theme_json_path = os.path.join(folder_path, "theme.json")
            if os.path.exists(theme_json_path):
                try:
                    with open(theme_json_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    # Convert icon mapping paths to absolute paths
                    resolved_icons = {}
                    for app_name, icon_filename in meta.get("icons", {}).items():
                        icon_path = os.path.join(folder_path, icon_filename)
                        if os.path.exists(icon_path):
                            resolved_icons[app_name] = icon_path.replace('\\', '/')
                            
                    theme_data = {
                        "id": folder_name,
                        "name": meta.get("name", folder_name),
                        "author": meta.get("author", "Unknown"),
                        "description": meta.get("description", ""),
                        "category": meta.get("category", "Custom"),
                        "icons": resolved_icons
                    }
                    themes.append(theme_data)
                except Exception as e:
                    logger.error(f"Failed to parse theme.json in {folder_name}: {e}")
                    
    return themes

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
    }

@app.post("/api/settings")
def save_app_settings(themeMode: str = Form(None), filterType: str = Form(None)):
    if themeMode:
        set_setting("themeMode", themeMode)
    if filterType:
        set_setting("filterType", filterType)
    return {"success": True}

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
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
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
        url_to_load = "http://localhost:5173"
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
            background_color="#121214"
        )
        webview.start()
    except Exception as e:
        logger.error(f"PyWebView failed to start: {e}")
        print(f"Error starting desktop window: {e}. Please ensure WebView2 Runtime is installed.")

if __name__ == "__main__":
    # If uvicorn runs this script as a subprocess (e.g. reload), do not spawn webview
    if "uvicorn" not in sys.argv[0]:
        main()
