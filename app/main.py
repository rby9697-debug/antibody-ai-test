from __future__ import annotations

import json
from sqlite3 import IntegrityError
from typing import Any

from app.models import Role, User
from app.services import ForbiddenError, db_backup, import_projects, list_projects, system_status


def parse_user(headers: dict[str, str] | None) -> User:
    headers = headers or {}
    role = headers.get("X-Role", Role.read_only)
    return User(username=headers.get("X-User", "system"), role=Role(role))


def handle_request(
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    user = parse_user(headers)
    try:
        if method == "GET" and path == "/projects":
            return 200, list_projects(user)
        if method == "POST" and path == "/projects/import":
            payload = body or {}
            imported = import_projects(user, payload.get("project_names", []))
            return 200, {"imported": imported}
        if method == "GET" and path == "/admin/db-backup":
            return 200, db_backup(user)
        if method == "GET" and path == "/system/status":
            return 200, system_status(user)
        return 404, {"detail": "Not Found"}
    except ForbiddenError:
        return 403, {"detail": "Forbidden"}
    except IntegrityError:
        return 400, {"detail": "Import failed and was rolled back"}


def application(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ.get("PATH_INFO", "/")
    headers = {
        "X-User": environ.get("HTTP_X_USER", "system"),
        "X-Role": environ.get("HTTP_X_ROLE", Role.read_only),
    }

    body = None
    if method == "POST":
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw = environ["wsgi.input"].read(length) if length else b"{}"
        body = json.loads(raw.decode("utf-8"))

    status_code, payload = handle_request(method, path, headers, body)
    start_response(f"{status_code} OK", [("Content-Type", "application/json")])
    return [json.dumps(payload).encode("utf-8")]
