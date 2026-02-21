# Template import mapping pre-check

Detected sheet names and structural header rows before implementing import logic:

| Sheet name | Header row |
| --- | --- |
| Project Master Data | 3 |
| Milestone Tracker | 2 |
| Sample Tracking | 2 |
| Execution Details | 2 |
| Lead Summary | 3 |

Mapping confirmation:
- `SG866-template.xlsx` and `SG888-template.xlsx` have the same sheet order.
- The detected structural header row index and header labels match for every sheet.
- Import mapping can therefore be shared between both templates.

To regenerate:
```bash
python scripts/inspect_template_headers.py
```
