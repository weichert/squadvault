-- 0001_add_canonical_tables.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS canonical_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  event_type TEXT NOT NULL,

  action_fingerprint TEXT NOT NULL,

  best_memory_event_id INTEGER NOT NULL,
  best_score INTEGER NOT NULL DEFAULT 0,

  selection_version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,

  FOREIGN KEY(best_memory_event_id) REFERENCES memory_events(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_canonical_action
ON canonical_events (league_id, season, event_type, action_fingerprint);

CREATE TABLE IF NOT EXISTS canonical_membership (
  canonical_event_id INTEGER NOT NULL,
  memory_event_id INTEGER NOT NULL,
  score INTEGER NOT NULL,

  PRIMARY KEY (canonical_event_id, memory_event_id),
  FOREIGN KEY(canonical_event_id) REFERENCES canonical_events(id),
  FOREIGN KEY(memory_event_id) REFERENCES memory_events(id)
);

CREATE INDEX IF NOT EXISTS ix_canonical_best
ON canonical_events (league_id, season, event_type, best_memory_event_id);
