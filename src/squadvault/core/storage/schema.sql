-- ============================================================================
-- SquadVault Schema (canonical)
--
-- This schema must match the fixture DB (fixtures/ci_squadvault.sqlite).
-- All tables, columns, and indexes defined here must exist in production.
-- Changes require versioned migration scripts in core/storage/migrations/.
-- ============================================================================

-- =========================
-- Memory layer (append-only)
-- =========================

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

CREATE INDEX IF NOT EXISTS ix_canonical_best
ON canonical_events (league_id, season, event_type, best_memory_event_id);

CREATE TABLE IF NOT EXISTS canonical_membership (
  canonical_event_id INTEGER NOT NULL,
  memory_event_id INTEGER NOT NULL,
  score INTEGER NOT NULL,

  PRIMARY KEY (canonical_event_id, memory_event_id),
  FOREIGN KEY(canonical_event_id) REFERENCES canonical_events(id),
  FOREIGN KEY(memory_event_id) REFERENCES memory_events(id)
);

-- Convenience view: best-selected memory event per canonical event
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
-- Directory tables (name resolution)
-- =========================

CREATE TABLE IF NOT EXISTS franchise_directory (
  league_id     TEXT    NOT NULL,
  season        INTEGER NOT NULL,
  franchise_id  TEXT    NOT NULL,

  name          TEXT,
  owner_name    TEXT,

  raw_json      TEXT,
  updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id, season, franchise_id)
);

CREATE INDEX IF NOT EXISTS idx_franchise_directory_lookup
  ON franchise_directory (league_id, season, franchise_id);

CREATE TABLE IF NOT EXISTS player_directory (
  league_id   TEXT    NOT NULL,
  season      INTEGER NOT NULL,
  player_id   TEXT    NOT NULL,

  name        TEXT,
  position    TEXT,
  team        TEXT,

  raw_json    TEXT,
  updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id, season, player_id)
);

CREATE INDEX IF NOT EXISTS idx_player_directory_lookup
  ON player_directory (league_id, season, player_id);

-- =========================
-- Recap artifacts (MVP)
-- =========================

CREATE TABLE IF NOT EXISTS recap_artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,

  artifact_type TEXT NOT NULL DEFAULT 'WEEKLY_RECAP',

  version INTEGER NOT NULL,

  -- lifecycle state machine: DRAFT | APPROVED | WITHHELD | SUPERSEDED
  state TEXT NOT NULL,

  -- deterministic provenance
  selection_fingerprint TEXT NOT NULL,
  window_start TEXT,
  window_end TEXT,

  -- optional output (WITHHELD may leave this NULL)
  rendered_text TEXT,

  -- governance metadata
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  created_by TEXT NOT NULL DEFAULT 'system',

  approved_at TEXT,
  approved_by TEXT,

  withheld_reason TEXT,

  supersedes_version INTEGER,

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

  -- State machine
  state TEXT NOT NULL,

  -- Selection traceability
  window_mode TEXT,
  window_start TEXT,
  window_end TEXT,
  selection_fingerprint TEXT NOT NULL,
  canonical_ids_json TEXT NOT NULL,
  counts_by_type_json TEXT NOT NULL,

  -- Regeneration + withhold reasons
  reason TEXT,

  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT,

  -- EAL v1 persistence
  editorial_attunement_v1 TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recap_runs_unique_week
ON recap_runs (league_id, season, week_index);

-- =========================
-- Recap selections (selection persistence)
-- =========================

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

-- =========================
-- Legacy recaps table
-- =========================

CREATE TABLE IF NOT EXISTS recaps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week_index INTEGER NOT NULL,

  recap_version INTEGER NOT NULL,
  selection_version INTEGER NOT NULL DEFAULT 1,

  selection_fingerprint TEXT NOT NULL,
  window_start TEXT,
  window_end TEXT,

  status TEXT NOT NULL,
  created_at TEXT NOT NULL,

  artifact_path TEXT,
  artifact_json TEXT,

  UNIQUE (league_id, season, week_index, recap_version)
);

CREATE INDEX IF NOT EXISTS ix_recaps_lookup
ON recaps (league_id, season, week_index);

-- =========================
-- Recap verdicts (generation decisions)
-- =========================

CREATE TABLE IF NOT EXISTS recap_verdicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  league_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  range_start TEXT NOT NULL,
  range_end TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT,
  inputs_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
