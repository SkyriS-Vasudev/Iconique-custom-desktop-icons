-- Schema for Iconique Database

CREATE TABLE IF NOT EXISTS backups (
    shortcut_path TEXT PRIMARY KEY,
    original_target_path TEXT,
    original_icon_location TEXT,
    backup_icon_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

