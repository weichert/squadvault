-- 001_create_recap_runs.sql
-- Minimal recap workflow hardening: persisted state + fingerprint per (league, season, week)

CREATE TABLE IF NOT EXISTS recap_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,

  -- State machine (minimal v1)
  state TEXT NOT NULL, -- ELIGIBLE | DRAFTED | REVIEW_REQUIRED | APPROVED | WITHHELD | SUPERSEDED

  -- Selection traceability
  window_mode TEXT,
  window_start TEXT,
  window_end TEXT,
  selection_fingerprint TEXT NOT NULL,
  canonical_ids_json TEXT NOT NULL,
  counts_by_type_json TEXT NOT NULL,

  -- Regeneration + withhold reasons
  reason TEXT,

  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Enforce "one active run per week" (you can relax later if needed).
CREATE UNIQUE INDEX IF NOT EXISTS idx_recap_runs_unique_week
ON recap_runs(league_id, season, week_index);
