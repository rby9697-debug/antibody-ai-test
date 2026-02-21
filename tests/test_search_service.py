from src.search_service import SEARCH_SQL, normalize_query, run_search


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = None

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchall(self):
        return self.rows


def test_normalize_query_wraps_like_tokens():
    assert normalize_query("abc") == "%abc%"


def test_run_search_returns_grouped_projects_and_hits():
    rows = [
        ("P-100", "projects", "project_id", "P-100", 100),
        ("P-100", "samples", "item_name", "Sample X", 50),
        ("P-200", "milestones", "status", "in_progress", 55),
    ]
    cursor = FakeCursor(rows)

    result = run_search(cursor, "P-", limit=20)

    assert cursor.executed[0] == SEARCH_SQL
    assert cursor.executed[1] == {"q": "%P-%", "limit": 20}
    assert result.projects == ["P-100", "P-200"]
    assert result.hits == [
        {"project_id": "P-100", "table": "projects", "field": "project_id", "snippet": "P-100"},
        {"project_id": "P-100", "table": "samples", "field": "item_name", "snippet": "Sample X"},
        {"project_id": "P-200", "table": "milestones", "field": "status", "snippet": "in_progress"},
    ]


def test_run_search_short_circuits_empty_query():
    cursor = FakeCursor([])
    result = run_search(cursor, "   ")

    assert result.projects == []
    assert result.hits == []
    assert cursor.executed is None
