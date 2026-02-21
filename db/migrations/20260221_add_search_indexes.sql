-- Search indexes for archive global search.

-- Optional extension for better fuzzy matching if we move from pure ILIKE to trigrams.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_project_fields_field_name_trgm
  ON project_fields USING gin (field_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_project_fields_field_value_trgm
  ON project_fields USING gin (field_value gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_milestones_name_trgm
  ON milestones USING gin (milestone_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_milestones_status_trgm
  ON milestones USING gin (status gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_samples_item_name_trgm
  ON samples USING gin (item_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_samples_lot_no_trgm
  ON samples USING gin (lot_no gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_samples_source_trgm
  ON samples USING gin (source gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_execution_steps_stage_trgm
  ON execution_steps USING gin (stage gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_execution_steps_step_action_trgm
  ON execution_steps USING gin (step_action gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_execution_steps_key_params_trgm
  ON execution_steps USING gin (key_params gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_execution_steps_operator_trgm
  ON execution_steps USING gin (operator gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lead_summary_final_candidate_trgm
  ON lead_summary USING gin (final_candidate_id gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lead_summary_parental_clone_trgm
  ON lead_summary USING gin (parental_clone_id gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_lead_summary_recommendation_trgm
  ON lead_summary USING gin (recommendation gin_trgm_ops);

-- Placeholder for future payload_json search acceleration.
-- CREATE INDEX IF NOT EXISTS idx_projects_payload_json_gin
--   ON projects USING gin (payload_json);
