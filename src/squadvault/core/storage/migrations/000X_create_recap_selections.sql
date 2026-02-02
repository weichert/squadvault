CREATE TABLE IF NOT EXISTS recap_selections (
  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,
  selection_version INTEGER NOT NULL DEFAULT 1,

  window_mode TEXT NOT NULL,
  window_start TEXT,
  window_end TEXT,

  event_count INTEGER NOT NULL,
  fingerprint TEXT NOT NULL,
  computed_at TEXT NOT NULL,

  PRIMARY KEY (league_id, season, week_index, selection_version)
);

CREATE INDEX IF NOT EXISTS ix_recap_sel_lookup
ON recap_selections (league_id, season, week_index);
