# Project health endpoint and audit logging specification

## Audit log writes

Create one `audit_logs` row for each successful call to:

- Import endpoint (`action = IMPORT`)
- Export endpoint (`action = EXPORT`)
- Restore endpoint (`action = RESTORE`)

Recommended payload:

- `actor`: authenticated username/email when available; otherwise `NULL`
- `project_id`: current project id
- `detail_json`: endpoint-specific metadata (e.g. file names, counts, restore snapshot id, duration)

## Health endpoint

`GET /projects/{project_id}/health`

Response shape:

```json
{
  "status": "ok|warning|error",
  "issues": [
    { "type": "missing_master_fields|expired_samples|milestone_completion_mismatch", "message": "..." }
  ]
}
```

Rules:

1. Required master fields missing -> add warning issue.
2. Expired samples -> add warning issue.
3. Milestone with `status=complete` but empty `actual_finish` -> add error issue.

Status derivation:

- `error` if any error issues.
- else `warning` if any warning issues.
- else `ok`.
