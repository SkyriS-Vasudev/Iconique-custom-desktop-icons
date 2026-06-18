import os
import subprocess
import json
import ctypes
import shutil
from backend.logging_config import logger
from backend.database import add_backup, get_backup, delete_backup, get_all_backups, add_history_entry

def get_cache_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    appdata = os.getenv('APPDATA')
    if appdata:
        cache_dir = os.path.join(appdata, 'Iconique', 'cache')
        try:
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except OSError:
            logger.warning("AppData cache directory is not writable; falling back to workspace cache.")

    cache_dir = os.path.join(base_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_backups_dir():
    """
    Resolve the active backup directory.

    The default location is %APPDATA%/Iconique/backups. If the user changes the
    backup location setting to "workspace", backups are stored inside the
    repository under backend/backups. When APPDATA is unavailable, we fall back
    to the workspace so the app still works in constrained environments.
    """
    from backend.database import get_setting

    backup_location = get_setting("backupLocation", "appdata")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_backups = os.path.join(base_dir, 'backups')

    if backup_location == "workspace":
        os.makedirs(workspace_backups, exist_ok=True)
        return workspace_backups

    appdata = os.getenv('APPDATA')
    if appdata:
        backups_dir = os.path.join(appdata, 'Iconique', 'backups')
        try:
            os.makedirs(backups_dir, exist_ok=True)
            return backups_dir
        except OSError:
            logger.warning("AppData backups directory is not writable; falling back to workspace backups.")

    os.makedirs(workspace_backups, exist_ok=True)
    return workspace_backups

def run_powershell(script):
    logger.debug(f"Executing PowerShell Script:\n{script}")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"PowerShell Script Failed (code {result.returncode}):\n{result.stderr}")
    return result.returncode == 0, result.stdout, result.stderr

def refresh_explorer():
    """
    Triggers a shell association change notification in Windows, which tells
    Windows Explorer to reload cached icons and redraw the desktop immediately.
    """
    try:
        # SHCNE_ASSOCCHANGED = 0x08000000
        # SHCNF_IDLIST = 0
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        logger.info("Shell notification SHChangeNotify sent successfully to refresh explorer icons.")
        return True
    except Exception as e:
        logger.error(f"Failed to call SHChangeNotify: {e}")
        return False

def discover_shortcuts():
    """
    Scans the User Desktop and Public Desktop for .lnk files, resolves them,
    and extracts their details.
    """
    logger.info("Scanning desktop directories for shortcuts...")
    
    cache_dir = get_cache_dir().replace('\\', '\\\\')
    
    ps_script = f"""
    Add-Type -AssemblyName System.Drawing
    $shell = New-Object -ComObject WScript.Shell
    
    $userDesktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
    $publicDesktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory)
    $desktops = @($userDesktop, $publicDesktop)
    $shortcuts = @()
    
    $cacheDir = "{cache_dir}"
    
    foreach ($dir in $desktops) {{
        if (Test-Path $dir) {{
            Get-ChildItem -Path $dir -Filter *.lnk | ForEach-Object {{
                try {{
                    $lnk = $shell.CreateShortcut($_.FullName)
                    $name = $_.BaseName
                    $safeName = $name -replace '[^a-zA-Z0-9_\\\\-]', '_'
                    $pngPath = Join-Path $cacheDir "$($safeName).png"
                    
                    # Resolve Target
                    $targetPath = $lnk.TargetPath
                    
                    # Resolve Icon Location
                    $iconLoc = $lnk.IconLocation
                    $sourcePath = ""
                    if ($iconLoc -and $iconLoc -ne ",0") {{
                        $parts = $iconLoc.Split(",")
                        $sourcePath = $parts[0]
                    }} else {{
                        $sourcePath = $targetPath
                    }}
                    
                    # Extract icon if it exists and cache as PNG
                    $extracted = $false
                    if ($sourcePath -and (Test-Path $sourcePath)) {{
                        try {{
                            $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($sourcePath)
                            $bmp = $icon.ToBitmap()
                            $bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
                            $bmp.Dispose()
                            $icon.Dispose()
                            $extracted = $true
                        }} catch {{
                            $extracted = $false
                        }}
                    }}
                    
                    # Check if target is a file or folder or URL
                    $isFolder = $false
                    if ($targetPath -and (Test-Path $targetPath -PathType Container)) {{
                        $isFolder = $true
                    }}
                    
                    $shortcuts += [PSCustomObject]@{{
                        name = $name
                        path = $_.FullName
                        targetPath = $targetPath
                        iconLocation = $iconLoc
                        iconCachePath = $pngPath
                        extracted = $extracted
                        isFolder = $isFolder
                    }}
                }} catch {{
                    # Continue silently on individual failure
                }}
            }}
        }}
    }}
    $shortcuts | ConvertTo-Json
    """
    
    success, stdout, stderr = run_powershell(ps_script)
    if not success or not stdout.strip():
        logger.warning("No shortcuts found or PowerShell script failed.")
        return []
        
    try:
        # Standardize json keys
        shortcuts = json.loads(stdout)
        # Ensure it is a list
        if not isinstance(shortcuts, list):
            shortcuts = [shortcuts]
            
        # Add customization status
        from backend.database import get_backup
        for s in shortcuts:
            bk = get_backup(s['path'])
            backup_exists = bk is not None
            s['isCustomized'] = backup_exists
            s['backupExists'] = backup_exists
            s['iconCacheUrl'] = f"/api/assets/cache/{os.path.basename(s['iconCachePath'])}"
            # Standardize path slashes for frontend
            s['iconCachePath'] = s['iconCachePath'].replace('\\', '/')
            s['path'] = s['path'].replace('\\', '/')
            s['targetPath'] = s['targetPath'].replace('\\', '/')
            
        logger.info(f"Discovered {len(shortcuts)} shortcuts.")
        return shortcuts
    except Exception as e:
        logger.error(f"Failed to parse shortcut json: {e}. Output was: {stdout}")
        return []

def apply_custom_icon(shortcut_path, custom_ico_path, action_type='applied_custom'):
    """
    Saves the original configuration (if not backed up), applies the custom icon,
    logs the change history, and refreshes the desktop.
    """
    shortcut_path = os.path.normpath(shortcut_path)
    custom_ico_path = os.path.normpath(custom_ico_path)
    
    if not os.path.exists(shortcut_path):
        logger.error(f"Shortcut does not exist: {shortcut_path}")
        return False, "Shortcut file not found."
        
    if not os.path.exists(custom_ico_path):
        logger.error(f"ICO file does not exist: {custom_ico_path}")
        return False, "Custom icon (.ico) file not found."
        
    # 1. Parse current shortcut info
    ps_read = f"""
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut("{shortcut_path.replace('"', '`"')}")
    [PSCustomObject]@{{
        TargetPath = $lnk.TargetPath
        IconLocation = $lnk.IconLocation
    }} | ConvertTo-Json
    """
    
    success, stdout, _ = run_powershell(ps_read)
    if not success or not stdout.strip():
        return False, "Failed to inspect current shortcut properties."
        
    try:
        props = json.loads(stdout)
        target_path = props.get('TargetPath', '')
        current_icon_location = props.get('IconLocation', '')
    except Exception as e:
        logger.error(f"Failed to read properties of {shortcut_path}: {e}")
        return False, f"Error inspecting shortcut properties: {e}"
        
    # 2. Backup if not already backed up
    existing_backup = get_backup(shortcut_path)
    shortcut_name = os.path.splitext(os.path.basename(shortcut_path))[0]
    
    if not existing_backup:
        # Extract the default icon first so we have a visual backup of what it looked like
        backups_dir = get_backups_dir()
        safe_name = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in shortcut_name])
        backup_png_path = os.path.join(backups_dir, f"{safe_name}_backup.png")
        
        # Determine extraction source
        source_path = target_path
        if current_icon_location and current_icon_location != ",0":
            parts = current_icon_location.split(",")
            source_path = parts[0]
            
        # Extract default icon
        ps_extract = f"""
        Add-Type -AssemblyName System.Drawing
        if ("{source_path}" -and (Test-Path "{source_path}")) {{
            try {{
                $icon = [System.Drawing.Icon]::ExtractAssociatedIcon("{source_path}")
                $bmp = $icon.ToBitmap()
                $bmp.Save("{backup_png_path.replace('\\', '\\\\')}", [System.Drawing.Imaging.ImageFormat]::Png)
                $bmp.Dispose()
                $icon.Dispose()
                Write-Output "SUCCESS"
            }} catch {{
                Write-Output "FAILED"
            }}
        }} else {{
            Write-Output "SOURCE_NOT_FOUND"
        }}
        """
        _, out, _ = run_powershell(ps_extract)
        
        # Save backup in database
        saved = add_backup(
            shortcut_path=shortcut_path,
            original_target_path=target_path,
            original_icon_location=current_icon_location,
            backup_icon_path=backup_png_path if "SUCCESS" in out else None
        )
        if not saved:
            logger.warning("Could not create database backup record. Proceeding anyway.")
            
    # 3. Apply custom icon via PowerShell
    ps_write = f"""
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut("{shortcut_path.replace('"', '`"')}")
    $lnk.IconLocation = "{custom_ico_path.replace('\\', '\\\\')},0"
    $lnk.Save()
    """
    
    success, _, stderr = run_powershell(ps_write)
    if not success:
        return False, f"Failed to modify shortcut properties: {stderr}"
        
    # 4. Record history
    add_history_entry(
        shortcut_path=shortcut_path,
        shortcut_name=shortcut_name,
        action=action_type,
        icon_path=custom_ico_path
    )
    
    # 5. Refresh explorer
    refresh_explorer()
    
    return True, "Icon applied successfully."

def restore_shortcut_icon(shortcut_path):
    """
    Restores the original icon of a single shortcut from its backup record.
    """
    shortcut_path = os.path.normpath(shortcut_path)
    bk = get_backup(shortcut_path)
    
    if not bk:
        logger.warning(f"No backup record found for {shortcut_path}")
        return False, "No backup record found. Icon is already at its default state or was never customized."
        
    if not os.path.exists(shortcut_path):
        return False, "Shortcut file does not exist."
        
    original_icon_location = bk.get('original_icon_location', '')
    if not original_icon_location:
        # Default behavior: if no custom icon location was set, we set it to empty
        original_icon_location = ""
        
    # Apply original icon location
    ps_restore = f"""
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut("{shortcut_path.replace('"', '`"')}")
    $lnk.IconLocation = "{original_icon_location.replace('\\', '\\\\')}"
    $lnk.Save()
    """
    
    success, _, stderr = run_powershell(ps_restore)
    if not success:
        return False, f"Failed to restore shortcut: {stderr}"
        
    # Add history
    shortcut_name = os.path.splitext(os.path.basename(shortcut_path))[0]
    add_history_entry(
        shortcut_path=shortcut_path,
        shortcut_name=shortcut_name,
        action='restored_original',
        icon_path=None
    )
    
    # Delete backup record
    delete_backup(shortcut_path)
    
    # Remove backup png if it exists
    backup_png = bk.get('backup_icon_path')
    if backup_png and os.path.exists(backup_png):
        try:
            os.remove(backup_png)
        except Exception as e:
            logger.warning(f"Could not delete backup PNG file: {e}")
            
    # Refresh explorer
    refresh_explorer()
    return True, "Original icon restored successfully."

def restore_all_shortcuts():
    """
    Restores every customized shortcut to its original configuration.
    """
    logger.info("Starting global restore of all shortcuts...")
    backups = get_all_backups()
    
    if not backups:
        logger.info("No shortcuts found to restore.")
        return True, "No customized shortcuts found."
        
    failures = []
    restored_count = 0
    
    for bk in backups:
        shortcut_path = bk['shortcut_path']
        success, msg = restore_shortcut_icon(shortcut_path)
        if success:
            restored_count += 1
        else:
            failures.append(f"{os.path.basename(shortcut_path)}: {msg}")
            
    if failures:
        logger.warning(f"Global restore completed with some errors. Restored {restored_count}/{len(backups)}")
        return False, f"Restored {restored_count} shortcuts, but {len(failures)} failed: " + ", ".join(failures)
        
    logger.info("Global restore completed successfully.")
    return True, f"All {restored_count} customized shortcuts restored to default."

def create_desktop_shortcut_and_modify(exe_path, app_name, custom_ico_path):
    """
    Creates a new desktop shortcut pointing to an executable, and applies the custom icon.
    Used when a user wants to customize an application that does not have a desktop shortcut.
    """
    exe_path = os.path.normpath(exe_path)
    custom_ico_path = os.path.normpath(custom_ico_path)
    
    if not os.path.exists(exe_path):
        return False, f"Target executable not found at: {exe_path}"
        
    # Get user desktop directory
    ps_get_desktop = "[Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)"
    success, stdout, _ = run_powershell(ps_get_desktop)
    if not success or not stdout.strip():
        return False, "Failed to resolve Desktop folder location."
        
    desktop_dir = stdout.strip()
    safe_app_name = "".join([c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in app_name]).strip()
    if not safe_app_name:
        safe_app_name = "New Shortcut"
    shortcut_path = os.path.join(desktop_dir, f"{safe_app_name}.lnk")
    
    if os.path.exists(shortcut_path):
        logger.warning(f"Shortcut already exists: {shortcut_path}. Overwriting icon.")
        
    # Create shortcut pointing to EXE
    ps_create = f"""
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut("{shortcut_path.replace('"', '`"')}")
    $lnk.TargetPath = "{exe_path.replace('\\', '\\\\')}"
    $lnk.WorkingDirectory = "{os.path.dirname(exe_path).replace('\\', '\\\\')}"
    $lnk.Save()
    """
    
    success, _, stderr = run_powershell(ps_create)
    if not success:
        return False, f"Failed to create desktop shortcut: {stderr}"
        
    # Apply custom icon to the newly created shortcut
    return apply_custom_icon(shortcut_path, custom_ico_path, action_type='applied_custom')
