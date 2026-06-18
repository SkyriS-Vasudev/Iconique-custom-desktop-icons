import os
import sqlite3
from datetime import datetime
from backend.logging_config import logger

def get_db_path():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_db_dir = backend_dir

    appdata = os.getenv('APPDATA')
    if appdata:
        db_dir = os.path.join(appdata, 'Iconique')
        try:
            os.makedirs(db_dir, exist_ok=True)
            return os.path.join(db_dir, 'iconique.db')
        except OSError:
            logger.warning("AppData database directory is not writable; falling back to the workspace.")

    os.makedirs(workspace_db_dir, exist_ok=True)
    return os.path.join(workspace_db_dir, 'iconique.db')

def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = get_db_path()
    logger.info(f"Initializing database at: {db_path}")
    
    # Read schema
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(backend_dir, 'schema.sql')
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}!")
        return False
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database schema initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

# Backup CRUD
def add_backup(shortcut_path, original_target_path, original_icon_location, backup_icon_path):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO backups 
            (shortcut_path, original_target_path, original_icon_location, backup_icon_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (shortcut_path, original_target_path, original_icon_location, backup_icon_path, datetime.now())
        )
        conn.commit()
        logger.info(f"Saved original icon backup for shortcut: {shortcut_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to add backup for {shortcut_path}: {e}")
        return False
    finally:
        conn.close()

def get_backup(shortcut_path):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM backups WHERE shortcut_path = ?",
            (shortcut_path,)
        ).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get backup for {shortcut_path}: {e}")
        return None
    finally:
        conn.close()

def delete_backup(shortcut_path):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM backups WHERE shortcut_path = ?", (shortcut_path,))
        conn.commit()
        logger.info(f"Deleted backup entry for shortcut: {shortcut_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete backup for {shortcut_path}: {e}")
        return False
    finally:
        conn.close()

def get_all_backups():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM backups").fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get all backups: {e}")
        return []
    finally:
        conn.close()



# Settings CRUD
def get_setting(key, default=None):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        ).fetchone()
        return row['value'] if row else default
    except Exception as e:
        logger.error(f"Failed to fetch setting {key}: {e}")
        return default
    finally:
        conn.close()

def set_setting(key, value):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        conn.commit()
        logger.debug(f"Setting updated: {key} = {value}")
        return True
    except Exception as e:
        logger.error(f"Failed to set setting {key}: {e}")
        return False
    finally:
        conn.close()
