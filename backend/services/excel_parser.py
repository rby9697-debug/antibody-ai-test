"""Excel parsing layer for SG866 workbook templates.

This module intentionally stays pure (no DB integration) and focuses only on
sheet/header detection + row extraction.
"""

from __future__ import annotations

import logging
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


@dataclass(frozen=True)
class SheetSpec:
    """Configuration used to detect and parse one sheet."""

    expected_header_first_cell: str


SHEET_SPECS: dict[str, SheetSpec] = {
    "Project Master Data": SheetSpec(expected_header_first_cell="分类 (Category)"),
    "Milestone Tracker": SheetSpec(expected_header_first_cell="里程碑编号"),
    "Sample Tracking": SheetSpec(expected_header_first_cell="物料/样品名称"),
    "Execution Details": SheetSpec(expected_header_first_cell="Project Stage"),
    "Lead Summary": SheetSpec(expected_header_first_cell="Final Candidate ID"),
}


def _column_to_index(column_letters: str) -> int:
    index = 0
    for char in column_letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index


def _normalize_header(value: str) -> str:
    return " ".join(value.replace("\n", " ").split())


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _read_workbook_xml(path: str | Path) -> tuple[list[str], dict[str, list[dict[int, Any]]]]:
    """Read workbook using stdlib only and return ordered row maps per sheet.

    Returns:
        (sheet_names, rows_by_sheet)
        rows_by_sheet[sheet_name] -> list of rows where each row is {column_index: value}
    """
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in shared_root.findall("main:si", NS):
                text = "".join(node.text or "" for node in si.findall(".//main:t", NS))
                shared_strings.append(text)

        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels_root}

        sheet_names: list[str] = []
        rows_by_sheet: dict[str, list[dict[int, Any]]] = {}

        for sheet in workbook_root.findall("main:sheets/main:sheet", NS):
            sheet_name = sheet.attrib["name"]
            rel_id = sheet.attrib[f"{{{NS['rel']}}}id"]
            target = rel_targets[rel_id]
            if not target.startswith("xl/"):
                target = f"xl/{target}"

            sheet_root = ET.fromstring(archive.read(target))
            rows: list[dict[int, Any]] = []

            for row in sheet_root.findall("main:sheetData/main:row", NS):
                row_values: dict[int, Any] = {}
                for cell in row.findall("main:c", NS):
                    ref = cell.attrib["r"]
                    col_match = re.match(r"([A-Z]+)", ref)
                    if not col_match:
                        continue
                    col_idx = _column_to_index(col_match.group(1))
                    value_node = cell.find("main:v", NS)
                    if value_node is None:
                        row_values[col_idx] = None
                        continue
                    raw_value = value_node.text
                    if cell.attrib.get("t") == "s" and raw_value is not None:
                        row_values[col_idx] = shared_strings[int(raw_value)]
                    else:
                        row_values[col_idx] = raw_value
                rows.append(row_values)

            sheet_names.append(sheet_name)
            rows_by_sheet[sheet_name] = rows

        return sheet_names, rows_by_sheet


def detect_header_row(rows: list[dict[int, Any]], spec: SheetSpec) -> int:
    """Detect header row index (1-based) for one sheet."""
    expected = spec.expected_header_first_cell.lower()
    for row_index, row in enumerate(rows, start=1):
        for value in row.values():
            if _is_empty(value):
                continue
            normalized = _normalize_header(str(value)).lower()
            if normalized.startswith(expected):
                return row_index
    raise ValueError(f"Unable to detect header row for expected marker: {spec.expected_header_first_cell}")


def _row_to_record(row: dict[int, Any], headers: list[tuple[int, str]], display_order: int) -> dict[str, Any]:
    record: dict[str, Any] = {"display_order": display_order}
    for col_index, header in headers:
        record[header] = row.get(col_index)
    return record


def _parse_sheet_rows(rows: list[dict[int, Any]], header_row_index: int) -> list[dict[str, Any]]:
    header_row = rows[header_row_index - 1]
    headers = [
        (col_index, _normalize_header(str(value)))
        for col_index, value in sorted(header_row.items())
        if not _is_empty(value)
    ]

    parsed_rows: list[dict[str, Any]] = []
    display_order = 1
    for row in rows[header_row_index:]:
        if all(_is_empty(row.get(col_index)) for col_index, _ in headers):
            break
        parsed_rows.append(_row_to_record(row=row, headers=headers, display_order=display_order))
        display_order += 1
    return parsed_rows


def parse_template_excel(path: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Parse all configured sheets and return dict[sheet_name] -> list[records]."""
    _, rows_by_sheet = _read_workbook_xml(path)
    parsed: dict[str, list[dict[str, Any]]] = {}

    for sheet_name, spec in SHEET_SPECS.items():
        if sheet_name not in rows_by_sheet:
            raise ValueError(f"Missing expected sheet: {sheet_name}")
        rows = rows_by_sheet[sheet_name]
        header_row_index = detect_header_row(rows=rows, spec=spec)
        parsed_rows = _parse_sheet_rows(rows=rows, header_row_index=header_row_index)
        logger.info(
            "Parsed sheet",
            extra={
                "sheet_name": sheet_name,
                "header_row_index": header_row_index,
                "rows_parsed": len(parsed_rows),
            },
        )
        parsed[sheet_name] = parsed_rows

    return parsed
