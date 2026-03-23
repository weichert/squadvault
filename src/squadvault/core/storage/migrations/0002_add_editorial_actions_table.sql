-- 0002_add_editorial_actions_table.sql
-- Adds the editorial_actions table for review workflow logging.
-- Safe for DBs that already have this table (uses IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS editorial_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,
  artifact_kind TEXT NOT NULL,
  artifact_version INTEGER NOT NULL,
  selection_fingerprint TEXT,
  action TEXT NOT NULL CHECK (action IN ('OPEN','APPROVE','REGENERATE','WITHHOLD','NOTES')),
  actor TEXT NOT NULL,
  notes_md TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_editorial_actions_lookup
ON editorial_actions (league_id, season, week_index, artifact_kind, artifact_version);
