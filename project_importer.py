import logging
from typing import Any, Callable

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

import excel_parser

LOGGER = logging.getLogger(__name__)


PARSER_FUNCTIONS: dict[str, tuple[str, ...]] = {
    "project_master_data": (
        "parse_project_master_data",
        "parse_project_master",
    ),
    "milestones": ("parse_milestones",),
    "samples": ("parse_samples",),
    "execution_steps": ("parse_execution_steps",),
    "lead_summary": ("parse_lead_summary",),
}

CHILD_TABLES = ("milestones", "samples", "execution_steps", "lead_summary")


def _get_parser(function_names: tuple[str, ...]) -> Callable[[str], Any]:
    for name in function_names:
        parser = getattr(excel_parser, name, None)
        if parser is not None:
            return parser
    raise AttributeError(f"No parser found for names: {', '.join(function_names)}")


def _extract_project_id(project_master_data: Any) -> Any:
    if isinstance(project_master_data, dict):
        return project_master_data.get("project_id") or project_master_data.get("Project ID")
    if isinstance(project_master_data, list):
        for row in project_master_data:
            if isinstance(row, dict) and ("project_id" in row or "Project ID" in row):
                return row.get("project_id") or row.get("Project ID")
    raise ValueError("Unable to extract project_id from Project Master Data")


def import_project(file_path: str, db: Session):
    parsed_data: dict[str, Any] = {}
    for sheet_key, parser_names in PARSER_FUNCTIONS.items():
        parser = _get_parser(parser_names)
        parsed_data[sheet_key] = parser(file_path)

    project_master_data = parsed_data["project_master_data"]
    project_id = _extract_project_id(project_master_data)
    if not project_id:
        raise ValueError("project_id is required")

    metadata = db.get_bind().metadata if hasattr(db.get_bind(), "metadata") else None
    if metadata is None:
        from sqlalchemy import MetaData

        metadata = MetaData()
        metadata.reflect(bind=db.get_bind())

    tables = metadata.tables

    if "projects" not in tables:
        raise ValueError("projects table not found")

    projects_table = tables["projects"]

    existing_project = db.execute(
        select(projects_table.c.project_id).where(projects_table.c.project_id == project_id)
    ).first()

    if existing_project:
        for child_table_name in CHILD_TABLES:
            if child_table_name in tables:
                db.execute(
                    delete(tables[child_table_name]).where(
                        tables[child_table_name].c.project_id == project_id
                    )
                )

        if isinstance(project_master_data, list):
            project_values = project_master_data[0]
        else:
            project_values = project_master_data

        db.execute(
            update(projects_table)
            .where(projects_table.c.project_id == project_id)
            .values(**project_values)
        )
    else:
        if isinstance(project_master_data, list):
            project_values = project_master_data[0]
        else:
            project_values = project_master_data
        db.execute(insert(projects_table).values(**project_values))

    inserted_counts: dict[str, int] = {}
    for child_table_name in CHILD_TABLES:
        rows = parsed_data.get(child_table_name) or []
        if child_table_name not in tables or not rows:
            inserted_counts[child_table_name] = 0
            continue

        prepared_rows = []
        for order, row in enumerate(rows, start=1):
            row_data = dict(row)
            row_data["project_id"] = project_id
            row_data.setdefault("display_order", order)
            prepared_rows.append(row_data)

        db.execute(insert(tables[child_table_name]), prepared_rows)
        inserted_counts[child_table_name] = len(prepared_rows)

    db.commit()

    LOGGER.info("Imported project_id=%s", project_id)
    for table_name, count in inserted_counts.items():
        LOGGER.info("Inserted rows: %s=%s", table_name, count)
