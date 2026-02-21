from pathlib import Path

from backend.services.excel_parser import SHEET_SPECS, parse_template_excel


def test_parse_template_excel_detects_all_5_sheets():
    parsed = parse_template_excel(Path("docs/templates/SG866-template.xlsx"))

    assert set(parsed.keys()) == set(SHEET_SPECS.keys())


def test_parse_template_excel_returns_expected_row_counts():
    parsed = parse_template_excel(Path("docs/templates/SG866-template.xlsx"))

    assert len(parsed["Project Master Data"]) == 19
    assert len(parsed["Milestone Tracker"]) == 6
    assert len(parsed["Sample Tracking"]) == 2
    assert len(parsed["Execution Details"]) == 7
    assert len(parsed["Lead Summary"]) == 0


def test_display_order_is_preserved():
    parsed = parse_template_excel(Path("docs/templates/SG866-template.xlsx"))

    milestone_orders = [row["display_order"] for row in parsed["Milestone Tracker"]]
    assert milestone_orders == [1, 2, 3, 4, 5, 6]

    first = parsed["Milestone Tracker"][0]
    assert first["里程碑编号"] == "M1"
    assert first["核心交付环节"] == "抗原准备与方案签字"
