from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def validate_project_integrity(project_id: str, db: Session) -> dict[str, Any]:
    issues: list[dict[str, str]] = []

    master = (
        db.execute(
            text(
                """
                SELECT project_name, owner, start_date
                FROM project_master
                WHERE project_id = :project_id
                """
            ),
            {"project_id": project_id},
        )
        .mappings()
        .first()
    )

    missing_fields: list[str] = []
    if master is None:
        missing_fields = ["project_name", "owner", "start_date"]
    else:
        for field in ("project_name", "owner", "start_date"):
            if _is_blank(master.get(field)):
                missing_fields.append(field)

    if missing_fields:
        issues.append(
            {
                "type": "missing_master_fields",
                "message": f"Missing required master fields: {', '.join(missing_fields)}",
            }
        )

    expired_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM samples
            WHERE project_id = :project_id
              AND expiry_date < :today
            """
        ),
        {"project_id": project_id, "today": date.today()},
    ).scalar()

    if expired_count:
        issues.append(
            {
                "type": "expired_samples",
                "message": f"Found {expired_count} expired sample(s)",
            }
        )

    orphaned_leads = db.execute(
        text(
            """
            SELECT ls.id
            FROM lead_summary ls
            LEFT JOIN execution_steps es ON es.lead_summary_id = ls.id
            WHERE ls.project_id = :project_id
              AND es.id IS NULL
            """
        ),
        {"project_id": project_id},
    ).mappings().all()

    if orphaned_leads:
        issues.append(
            {
                "type": "lead_summary_without_execution",
                "message": (
                    "Lead summary entries without matching execution steps: "
                    + ", ".join(str(row["id"]) for row in orphaned_leads)
                ),
            }
        )

    milestone_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM milestones
            WHERE project_id = :project_id
              AND is_complete = true
              AND completion_date IS NULL
            """
        ),
        {"project_id": project_id},
    ).scalar()

    if milestone_count:
        issues.append(
            {
                "type": "complete_milestone_missing_completion_date",
                "message": (
                    f"Found {milestone_count} completed milestone(s) without completion date"
                ),
            }
        )

    error_types = {"missing_master_fields", "lead_summary_without_execution"}
    if not issues:
        status = "ok"
    elif any(issue["type"] in error_types for issue in issues):
        status = "error"
    else:
        status = "warning"

    return {"status": status, "issues": issues}
