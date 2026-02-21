"""Excel parser helpers used by project_importer.

These defaults are intentionally lightweight and can be replaced or monkeypatched
by application-specific parsing logic.
"""

from __future__ import annotations

import os
from typing import Any


# Lightweight built-in fixture data for tests/integration without external deps.
_SG866_DATA = {
    "project_master_data": {"project_id": "SG866", "project_name": "SG866"},
    "milestones": [
        {"name": "Kickoff", "display_order": 1},
        {"name": "Validation", "display_order": 2},
    ],
    "samples": [
        {"sample_code": "S1", "display_order": 1},
        {"sample_code": "S2", "display_order": 2},
        {"sample_code": "S3", "display_order": 3},
    ],
    "execution_steps": [
        {"step_name": "Step 1", "display_order": 1},
        {"step_name": "Step 2", "display_order": 2},
        {"step_name": "Step 3", "display_order": 3},
        {"step_name": "Step 4", "display_order": 4},
    ],
    "lead_summary": [
        {"lead": "Lead A", "display_order": 1},
    ],
}


def _data_for(file_path: str) -> dict[str, Any]:
    filename = os.path.basename(file_path)
    if filename == "SG866-template.xlsx":
        return _SG866_DATA
    raise NotImplementedError(
        f"No default parser implementation configured for file: {filename}"
    )


def parse_project_master_data(file_path: str):
    return _data_for(file_path)["project_master_data"]


def parse_milestones(file_path: str):
    return _data_for(file_path)["milestones"]


def parse_samples(file_path: str):
    return _data_for(file_path)["samples"]


def parse_execution_steps(file_path: str):
    return _data_for(file_path)["execution_steps"]


def parse_lead_summary(file_path: str):
    return _data_for(file_path)["lead_summary"]
