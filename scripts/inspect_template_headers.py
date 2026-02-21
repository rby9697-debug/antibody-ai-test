#!/usr/bin/env python3
"""Print sheet names and detected header rows for SG template workbooks."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass
class SheetInspection:
    name: str
    header_row: int | None
    header_values: list[str]


def _col_to_index(cell_ref: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_ref).group(1)
    value = 0
    for char in letters:
        value = (value * 26) + (ord(char) - 64)
    return value


def _shared_strings(xlsx: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in xlsx.namelist():
        return []

    root = ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in root.findall("main:si", NS):
        values.append("".join((node.text or "") for node in si.findall(".//main:t", NS)))
    return values


def _sheet_targets(xlsx: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(xlsx.read("xl/workbook.xml"))
    rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("rel:Relationship", NS)}

    out: list[tuple[str, str]] = []
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        name = sheet.attrib["name"]
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[rid]
        out.append((name, target if target.startswith("xl/") else f"xl/{target}"))
    return out


def _row_values(row: ET.Element, shared: list[str]) -> dict[int, str]:
    values: dict[int, str] = {}
    for cell in row.findall("main:c", NS):
        idx = _col_to_index(cell.attrib.get("r", "A1"))
        inline = cell.find("main:is/main:t", NS)
        v = cell.find("main:v", NS)
        cell_type = cell.attrib.get("t")

        text = ""
        if inline is not None:
            text = inline.text or ""
        elif v is not None:
            raw = v.text or ""
            if cell_type == "s" and raw.isdigit() and int(raw) < len(shared):
                text = shared[int(raw)]
            else:
                text = raw

        if text.strip():
            values[idx] = text.strip()
    return values


def _detect_header(sheet_xml: bytes, shared: list[str]) -> tuple[int | None, list[str]]:
    root = ET.fromstring(sheet_xml)
    rows = root.findall("main:sheetData/main:row", NS)

    for row in rows:
        values = _row_values(row, shared)
        if len(values) >= 3:
            max_idx = max(values)
            return int(row.attrib.get("r", "0")), [values.get(i, "") for i in range(1, max_idx + 1)]

    return None, []


def inspect_workbook(path: Path) -> list[SheetInspection]:
    with zipfile.ZipFile(path) as xlsx:
        shared = _shared_strings(xlsx)
        inspections: list[SheetInspection] = []
        for name, target in _sheet_targets(xlsx):
            header_row, header_values = _detect_header(xlsx.read(target), shared)
            inspections.append(SheetInspection(name=name, header_row=header_row, header_values=header_values))
        return inspections


def main() -> None:
    base = Path("docs/templates")
    template_paths = [base / "SG866-template.xlsx", base / "SG888-template.xlsx"]

    all_results: dict[str, list[SheetInspection]] = {}
    for template in template_paths:
        results = inspect_workbook(template)
        all_results[str(template)] = results
        print(f"FILE: {template}")
        print(f"SHEETS: {[sheet.name for sheet in results]}")
        for sheet in results:
            print(f"  - {sheet.name}: header_row={sheet.header_row}, headers={sheet.header_values}")
        print()

    first = next(iter(all_results.values()))
    mapping_consistent = all(
        [(a.name, a.header_row, a.header_values) for a in inspection]
        == [(b.name, b.header_row, b.header_values) for b in first]
        for inspection in all_results.values()
    )
    print(f"MAPPING_CONSISTENT={mapping_consistent}")


if __name__ == "__main__":
    main()
