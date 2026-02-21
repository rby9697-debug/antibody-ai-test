from datetime import datetime, timedelta, timezone

from app import Project, handle_request, projects


def reset_projects() -> None:
    projects.clear()
    projects.update(
        {
            1: Project(id=1, name="Example Project"),
            2: Project(id=2, name="Paused Project", is_active=False),
        }
    )


def valid_master() -> dict[str, str]:
    return {
        "Project ID": "P-123",
        "Project Name": "A Project",
        "Client Name": "Client",
        "Target Name": "Target",
        "Core Screening Route": "Route-1",
    }


def test_import_rejected_when_project_locked() -> None:
    reset_projects()
    handle_request("POST", "/projects/1/lock", {"locked_by": "qa"})

    status, body = handle_request(
        "POST",
        "/projects/1/import",
        {"master": valid_master(), "samples": []},
    )

    assert status == 403
    assert body["detail"] == "Project is locked"


def test_import_requires_master_fields() -> None:
    reset_projects()
    master = valid_master()
    del master["Client Name"]

    status, body = handle_request("POST", "/projects/1/import", {"master": master, "samples": []})

    assert status == 422
    assert body["detail"]["message"] == "Missing required master fields"
    assert body["detail"]["missing_fields"] == ["Client Name"]


def test_lock_and_unlock_endpoints() -> None:
    reset_projects()

    lock_status, lock_body = handle_request("POST", "/projects/1/lock", {"locked_by": "user-1"})
    unlock_status, unlock_body = handle_request("POST", "/projects/1/unlock")

    assert lock_status == 200
    assert lock_body["is_locked"] is True
    assert lock_body["locked_by"] == "user-1"
    assert lock_body["locked_at"] is not None

    assert unlock_status == 200
    assert unlock_body["is_locked"] is False
    assert unlock_body["locked_by"] is None
    assert unlock_body["locked_at"] is None


def test_dashboard_summary_counts() -> None:
    reset_projects()
    projects[1].warnings.append("sample warning")
    projects[1].is_locked = True
    projects[1].samples.append(
        {"id": "s1", "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}
    )
    projects[1].samples.append(
        {"id": "s2", "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}
    )

    status, body = handle_request("GET", "/dashboard/summary")

    assert status == 200
    assert body == {
        "total_projects": 2,
        "active_projects": 1,
        "locked_projects": 1,
        "projects_with_warnings": 1,
        "expired_samples_count": 1,
    }
