from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/app.db")
BACKUP_DIR = Path("backups")
SYSTEM_VERSION = "internal-1.0"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_time TEXT NOT NULL
            )
            """
        )


def get_connection() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def safe_backup() -> Path:
    init_db()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = BACKUP_DIR / f"app-{timestamp}.db"
    temp = backup_path.with_suffix(".tmp")
    shutil.copy2(DB_PATH, temp)
    temp.replace(backup_path)

    with get_connection() as conn:
        conn.execute("INSERT INTO backup_logs(backup_time) VALUES (?)", (datetime.now(timezone.utc).isoformat(),))
    return backup_path
