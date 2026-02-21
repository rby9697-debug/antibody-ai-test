"""Global search service for internal archive."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SEARCH_SQL = """
WITH search_input AS (
  SELECT %(q)s::text AS q
),
all_hits AS (
  SELECT
    p.project_id,
    'projects'::text AS table_name,
    'project_id'::text AS field_name,
    p.project_id::text AS snippet,
    CASE WHEN p.project_id::text ILIKE si.q THEN 100 ELSE 80 END AS rank
  FROM projects p
  CROSS JOIN search_input si
  WHERE p.project_id::text ILIKE si.q

  UNION ALL

  SELECT
    pf.project_id,
    'project_fields',
    CASE
      WHEN pf.field_name ILIKE si.q THEN 'field_name'
      ELSE 'field_value'
    END,
    COALESCE(pf.field_name, '') || ': ' || COALESCE(pf.field_value, ''),
    60
  FROM project_fields pf
  CROSS JOIN search_input si
  WHERE pf.field_name ILIKE si.q OR pf.field_value ILIKE si.q

  UNION ALL

  SELECT
    m.project_id,
    'milestones',
    CASE WHEN m.milestone_name ILIKE si.q THEN 'milestone_name' ELSE 'status' END,
    COALESCE(m.milestone_name, '') || ' (' || COALESCE(m.status, '') || ')',
    55
  FROM milestones m
  CROSS JOIN search_input si
  WHERE m.milestone_name ILIKE si.q OR m.status ILIKE si.q

  UNION ALL

  SELECT
    s.project_id,
    'samples',
    CASE
      WHEN s.item_name ILIKE si.q THEN 'item_name'
      WHEN s.lot_no ILIKE si.q THEN 'lot_no'
      ELSE 'source'
    END,
    COALESCE(s.item_name, '') || ' / ' || COALESCE(s.lot_no, '') || ' / ' || COALESCE(s.source, ''),
    50
  FROM samples s
  CROSS JOIN search_input si
  WHERE s.item_name ILIKE si.q OR s.lot_no ILIKE si.q OR s.source ILIKE si.q

  UNION ALL

  SELECT
    es.project_id,
    'execution_steps',
    CASE
      WHEN es.stage ILIKE si.q THEN 'stage'
      WHEN es.step_action ILIKE si.q THEN 'step_action'
      WHEN es.key_params ILIKE si.q THEN 'key_params'
      ELSE 'operator'
    END,
    COALESCE(es.stage, '') || ' -> ' || COALESCE(es.step_action, '') || ' / ' || COALESCE(es.key_params, '') || ' / ' || COALESCE(es.operator, ''),
    45
  FROM execution_steps es
  CROSS JOIN search_input si
  WHERE es.stage ILIKE si.q
     OR es.step_action ILIKE si.q
     OR es.key_params ILIKE si.q
     OR es.operator ILIKE si.q

  UNION ALL

  SELECT
    ls.project_id,
    'lead_summary',
    CASE
      WHEN ls.final_candidate_id ILIKE si.q THEN 'final_candidate_id'
      WHEN ls.parental_clone_id ILIKE si.q THEN 'parental_clone_id'
      ELSE 'recommendation'
    END,
    COALESCE(ls.final_candidate_id, '') || ' / ' || COALESCE(ls.parental_clone_id, '') || ' / ' || COALESCE(ls.recommendation, ''),
    45
  FROM lead_summary ls
  CROSS JOIN search_input si
  WHERE ls.final_candidate_id ILIKE si.q
     OR ls.parental_clone_id ILIKE si.q
     OR ls.recommendation ILIKE si.q
)
SELECT project_id, table_name, field_name, snippet, rank
FROM all_hits
ORDER BY rank DESC, project_id
LIMIT %(limit)s;
""".strip()


@dataclass
class SearchResult:
    projects: list[str]
    hits: list[dict[str, Any]]


def normalize_query(q: str) -> str:
    raw = (q or "").strip()
    return f"%{raw}%"


def run_search(cursor: Any, q: str, limit: int = 100) -> SearchResult:
    if not q or not q.strip():
        return SearchResult(projects=[], hits=[])

    cursor.execute(SEARCH_SQL, {"q": normalize_query(q), "limit": limit})
    rows = cursor.fetchall()

    hits = [
        {
            "project_id": row[0],
            "table": row[1],
            "field": row[2],
            "snippet": row[3],
        }
        for row in rows
    ]

    seen = set()
    projects: list[str] = []
    for hit in hits:
        project_id = hit["project_id"]
        if project_id not in seen:
            seen.add(project_id)
            projects.append(project_id)

    return SearchResult(projects=projects, hits=hits)
