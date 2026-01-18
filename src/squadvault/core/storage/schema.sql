CREATE TABLE IF NOT EXISTS memory_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- identity / partitioning
  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,

  -- event identity + dedupe
  external_source TEXT NOT NULL,
  external_id TEXT NOT NULL,

  -- semantics
  event_type TEXT NOT NULL,

  -- time
  occurred_at TEXT,          -- ISO-8601 "Z" string
  ingested_at TEXT NOT NULL, -- ISO-8601 "Z" string

  -- data
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  event_type TEXT NOT NULL,

  action_fingerprint TEXT NOT NULL,

  -- pointer to ledger "winner"
  best_memory_event_id INTEGER NOT NULL,
  best_score INTEGER NOT NULL DEFAULT 0,

  -- bookkeeping
  selection_version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  occurred_at TEXT,

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

CREATE UNIQUE INDEX IF NOT EXISTS ux_memory_events_source_id
ON memory_events (external_source, external_id);

CREATE INDEX IF NOT EXISTS ix_memory_events_league_season_time
ON memory_events (league_id, season, occurred_at);

-- =========================
-- Canonical event layer
-- =========================

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

-- ------------------------------------------------------------
-- Canonical convenience view: best-selected memory event
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_canonical_best_events;

CREATE VIEW v_canonical_best_events AS
SELECT
  ce.id                         AS canonical_event_id,
  ce.league_id                  AS league_id,
  ce.season                     AS season,
  ce.event_type                 AS event_type,
  ce.action_fingerprint         AS action_fingerprint,
  ce.best_memory_event_id       AS best_memory_event_id,
  ce.best_score                 AS best_score,
  ce.selection_version          AS selection_version,
  ce.updated_at                 AS canonical_updated_at,

  me.external_source            AS external_source,
  me.external_id                AS external_id,
  me.occurred_at                AS occurred_at,
  me.ingested_at                AS ingested_at,
  me.payload_json               AS payload_json

FROM canonical_events ce
JOIN memory_events me
  ON me.id = ce.best_memory_event_id;

-- =========================
-- Recap artifacts (MVP)
-- =========================

CREATE TABLE IF NOT EXISTS recap_artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,

  artifact_type TEXT NOT NULL DEFAULT 'WEEKLY_RECAP', -- future-proof but fixed for MVP

  version INTEGER NOT NULL, -- 1..n per (league, season, week, type)

  -- lifecycle state machine: DRAFT | APPROVED | WITHHELD | SUPERSEDED
  state TEXT NOT NULL,

  -- deterministic provenance
  selection_fingerprint TEXT NOT NULL,  -- sha256 of ordered canonical_ids
  window_start TEXT,                    -- ISO-8601
  window_end TEXT,                      -- ISO-8601

  -- optional output (WITHHELD may leave this NULL)
  rendered_text TEXT,

  -- governance metadata
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL DEFAULT 'system',

  approved_at TEXT,
  approved_by TEXT,

  withheld_reason TEXT,

  supersedes_version INTEGER,

  -- hard safety: keep versions unique per week
  UNIQUE (league_id, season, week_index, artifact_type, version)
);

CREATE INDEX IF NOT EXISTS ix_recap_artifacts_lookup
ON recap_artifacts (league_id, season, week_index, artifact_type, version);

CREATE INDEX IF NOT EXISTS ix_recap_artifacts_state
ON recap_artifacts (league_id, season, state);

-- =========================
-- Recap runs (process ledger)
-- =========================

CREATE TABLE IF NOT EXISTS recap_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,

  artifact_type TEXT NOT NULL DEFAULT 'WEEKLY_RECAP',
  artifact_version INTEGER NOT NULL, -- foreign-key-ish pointer to recap_artifacts.version

  -- run bookkeeping
  state TEXT NOT NULL,               -- e.g., STARTED | COMPLETED | FAILED (keep boring)
  reason TEXT,                       -- optional freeform
  selection_fingerprint TEXT NOT NULL,

  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_recap_runs_lookup
ON recap_runs (league_id, season, week_index, artifact_type, artifact_version);

