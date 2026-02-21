from datetime import date

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.validation.project_health import validate_project_integrity


class FakeMappingsResult:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def mappings(self):
        return FakeMappingsResult(self._rows)

    def scalar(self):
        return self._scalar


class FakeSession:
    def __init__(self, *, master=None, expired_count=0, orphaned_leads=None, milestone_count=0):
        self.master = master
        self.expired_count = expired_count
        self.orphaned_leads = orphaned_leads or []
        self.milestone_count = milestone_count

    def execute(self, stmt, params):
        query = str(stmt)
        if "FROM project_master" in query:
            rows = [] if self.master is None else [self.master]
            return FakeResult(rows=rows)
        if "FROM samples" in query:
            assert params["today"] <= date.today()
            return FakeResult(scalar=self.expired_count)
        if "FROM lead_summary" in query:
            return FakeResult(rows=self.orphaned_leads)
        if "FROM milestones" in query:
            return FakeResult(scalar=self.milestone_count)
        raise AssertionError(f"Unexpected query: {query}")


def test_validate_project_integrity_ok_status():
    db = FakeSession(
        master={"project_name": "P1", "owner": "Alice", "start_date": "2024-01-01"},
    )

    payload = validate_project_integrity("P1", db)

    assert payload == {"status": "ok", "issues": []}


def test_validate_project_integrity_returns_all_issues():
    db = FakeSession(
        master={"project_name": "P1", "owner": "", "start_date": None},
        expired_count=2,
        orphaned_leads=[{"id": 10}, {"id": 22}],
        milestone_count=1,
    )

    payload = validate_project_integrity("P1", db)

    assert payload["status"] == "error"
    assert {issue["type"] for issue in payload["issues"]} == {
        "missing_master_fields",
        "expired_samples",
        "lead_summary_without_execution",
        "complete_milestone_missing_completion_date",
    }


def test_get_project_health_endpoint():
    fake_db = FakeSession(master={"project_name": "P1", "owner": "Alice", "start_date": "2024-01-01"})

    def override_get_db():
        return fake_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/projects/P1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "issues": []}

    app.dependency_overrides.clear()
