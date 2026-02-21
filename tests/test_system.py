from pathlib import Path

from app.database import BACKUP_DIR, DB_PATH, get_connection, init_db
from app.main import handle_request


def reset_state() -> None:
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM projects")
        conn.execute("DELETE FROM backup_logs")
        conn.execute("DELETE FROM users")
        conn.commit()
    for p in BACKUP_DIR.glob("*.db"):
        p.unlink()


def test_rbac_blocks_read_only_import() -> None:
    reset_state()
    status, payload = handle_request(
        "POST",
        "/projects/import",
        headers={"X-Role": "read_only", "X-User": "viewer"},
        body={"project_names": ["P1"]},
    )
    assert status == 403
    assert payload["detail"] == "Forbidden"


def test_import_is_transactional_on_failure() -> None:
    reset_state()
    status, payload = handle_request(
        "POST",
        "/projects/import",
        headers={"X-Role": "admin", "X-User": "root"},
        body={"project_names": ["DUP", "DUP"]},
    )
    assert status == 400
    assert payload["detail"] == "Import failed and was rolled back"

    with get_connection() as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    assert remaining == 0


def test_admin_backup_endpoint_creates_copy() -> None:
    reset_state()
    status, payload = handle_request(
        "GET",
        "/admin/db-backup",
        headers={"X-Role": "admin", "X-User": "root"},
    )
    assert status == 200
    assert Path(payload["backup_file"]).exists()


def test_system_status_returns_required_fields() -> None:
    reset_state()
    status, _ = handle_request(
        "POST",
        "/projects/import",
        headers={"X-Role": "project_manager", "X-User": "pm"},
        body={"project_names": ["P1", "P2"]},
    )
    assert status == 200

    handle_request("GET", "/admin/db-backup", headers={"X-Role": "admin", "X-User": "root"})
    status, payload = handle_request(
        "GET",
        "/system/status",
        headers={"X-Role": "scientist", "X-User": "sci"},
    )
    assert status == 200
    assert payload["total_projects"] == 2
    assert isinstance(payload["db_size_mb"], float)
    assert payload["last_backup_time"] is not None
    assert payload["system_version"] == "internal-1.0"
