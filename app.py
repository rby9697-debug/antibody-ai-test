from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


REQUIRED_MASTER_FIELDS = [
    "Project ID",
    "Project Name",
    "Client Name",
    "Target Name",
    "Core Screening Route",
]


@dataclass
class Project:
    id: int
    name: str
    is_active: bool = True
    is_locked: bool = False
    locked_at: datetime | None = None
    locked_by: str | None = None
    warnings: list[str] = field(default_factory=list)
    samples: list[dict[str, Any]] = field(default_factory=list)


projects: dict[int, Project] = {
    1: Project(id=1, name="Example Project"),
    2: Project(id=2, name="Paused Project", is_active=False),
}


def _get_project(project_id: int) -> Project | None:
    return projects.get(project_id)


def _serialize_project_lock(project: Project) -> dict[str, Any]:
    return {
        "project_id": project.id,
        "is_locked": project.is_locked,
        "locked_at": project.locked_at.isoformat() if project.locked_at else None,
        "locked_by": project.locked_by,
    }


def handle_request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    payload = payload or {}
    method = method.upper()

    if method == "POST" and path.startswith("/projects/") and path.endswith("/import"):
        project_id = int(path.split("/")[2])
        project = _get_project(project_id)
        if project is None:
            return 404, {"detail": "Project not found"}
        if project.is_locked:
            return 403, {"detail": "Project is locked"}

        master = payload.get("master", {})
        missing_fields = [field for field in REQUIRED_MASTER_FIELDS if not master.get(field)]
        if missing_fields:
            return 422, {
                "detail": {
                    "message": "Missing required master fields",
                    "missing_fields": missing_fields,
                }
            }

        samples = payload.get("samples", [])
        project.samples.extend(samples)
        return 200, {"status": "ok", "imported_samples": len(samples)}

    if method == "POST" and path.startswith("/projects/") and path.endswith("/lock"):
        project_id = int(path.split("/")[2])
        project = _get_project(project_id)
        if project is None:
            return 404, {"detail": "Project not found"}
        project.is_locked = True
        project.locked_at = datetime.now(timezone.utc)
        project.locked_by = payload.get("locked_by")
        return 200, _serialize_project_lock(project)

    if method == "POST" and path.startswith("/projects/") and path.endswith("/unlock"):
        project_id = int(path.split("/")[2])
        project = _get_project(project_id)
        if project is None:
            return 404, {"detail": "Project not found"}
        project.is_locked = False
        project.locked_at = None
        project.locked_by = None
        return 200, _serialize_project_lock(project)

    if method == "GET" and path == "/dashboard/summary":
        all_projects = list(projects.values())
        now = datetime.now(timezone.utc)
        expired_samples_count = 0

        for project in all_projects:
            for sample in project.samples:
                expires_at = sample.get("expires_at")
                if not expires_at:
                    continue
                expiry = datetime.fromisoformat(expires_at)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry < now:
                    expired_samples_count += 1

        return 200, {
            "total_projects": len(all_projects),
            "active_projects": sum(1 for project in all_projects if project.is_active),
            "locked_projects": sum(1 for project in all_projects if project.is_locked),
            "projects_with_warnings": sum(1 for project in all_projects if project.warnings),
            "expired_samples_count": expired_samples_count,
        }

    return 404, {"detail": "Not found"}
