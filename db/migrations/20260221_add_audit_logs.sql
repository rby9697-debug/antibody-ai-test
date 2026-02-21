CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actor TEXT NULL,
  action TEXT NOT NULL CHECK (action IN ('IMPORT', 'EXPORT', 'RESTORE', 'UPDATE')),
  project_id BIGINT NOT NULL,
  detail_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_project_id_created_at
  ON audit_logs (project_id, created_at DESC);
