from __future__ import annotations

from app.database import DB_PATH, SYSTEM_VERSION, get_connection, safe_backup
from app.models import Role, User


class ForbiddenError(Exception):
    pass


def require_role(user: User, allowed: set[Role]) -> None:
    if user.role not in allowed:
        raise ForbiddenError("Forbidden")


def list_projects(user: User) -> list[dict]:
    require_role(user, {Role.admin, Role.project_manager, Role.scientist, Role.read_only})
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM projects ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def import_projects(user: User, project_names: list[str]) -> int:
    require_role(user, {Role.admin, Role.project_manager})
    with get_connection() as conn:
        try:
            conn.execute("BEGIN")
            for name in project_names:
                conn.execute("INSERT INTO projects(name) VALUES (?)", (name,))
            conn.commit()
            return len(project_names)
        except Exception:
            conn.rollback()
            raise


def db_backup(user: User) -> dict[str, str]:
    require_role(user, {Role.admin})
    backup_path = safe_backup()
    return {"backup_file": str(backup_path)}


def system_status(user: User) -> dict:
    require_role(user, {Role.admin, Role.project_manager, Role.scientist, Role.read_only})
    with get_connection() as conn:
        total_projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        last_backup = conn.execute("SELECT MAX(backup_time) FROM backup_logs").fetchone()[0]

    db_size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 4) if DB_PATH.exists() else 0.0
    return {
        "total_projects": total_projects,
        "db_size_mb": db_size_mb,
        "last_backup_time": last_backup,
        "system_version": SYSTEM_VERSION,
    }
