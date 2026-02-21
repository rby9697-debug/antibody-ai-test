from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.orm import Session

from project_importer import import_project


def _create_schema(metadata: MetaData):
    Table(
        "projects",
        metadata,
        Column("project_id", String, primary_key=True),
        Column("project_name", String),
    )
    Table(
        "milestones",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", String, nullable=False),
        Column("name", String),
        Column("display_order", Integer),
    )
    Table(
        "samples",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", String, nullable=False),
        Column("sample_code", String),
        Column("display_order", Integer),
    )
    Table(
        "execution_steps",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", String, nullable=False),
        Column("step_name", String),
        Column("display_order", Integer),
    )
    Table(
        "lead_summary",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", String, nullable=False),
        Column("lead", String),
        Column("display_order", Integer),
    )


def test_import_sg866_template_row_counts():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata = MetaData()
    _create_schema(metadata)
    metadata.create_all(engine)

    template_path = str(Path("docs/templates/SG866-template.xlsx"))

    with Session(engine) as session:
        import_project(template_path, session)

        projects = session.execute(select(metadata.tables["projects"])).all()
        milestones = session.execute(select(metadata.tables["milestones"])).all()
        samples = session.execute(select(metadata.tables["samples"])).all()
        execution_steps = session.execute(select(metadata.tables["execution_steps"])).all()
        lead_summary = session.execute(select(metadata.tables["lead_summary"])).all()

    assert len(projects) == 1
    assert len(milestones) == 2
    assert len(samples) == 3
    assert len(execution_steps) == 4
    assert len(lead_summary) == 1
