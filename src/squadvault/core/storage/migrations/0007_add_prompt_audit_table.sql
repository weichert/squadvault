-- Migration 0007: prompt_audit observation sidecar table.
--
-- Append-only capture of prompt attempts emitted by the Writing Room
-- lifecycle (one row per retry attempt inside _generate_draft). Observation
-- sidecar — never feeds back into facts, never alters drafts, never gates
-- publication. Writes are env-gated on SQUADVAULT_PROMPT_AUDIT=1 from the
-- application layer; this migration only ensures the table exists.
--
-- This migration mirrors the standalone schema file at
-- src/squadvault/core/storage/schema_prompt_audit.sql, which is used by the
-- test fixture to materialize a throwaway audit DB. The two are kept in
-- lockstep deliberately: the standalone file lets tests stand up isolated
-- audit DBs without running the full migration framework, and this
-- migration is the canonical install path for the production DB.
--
-- v2 contract:
--   * No `version` column.
--   * No UNIQUE constraint — append-only by structure; duplicate
--     (league_id, season, week_index, attempt) tuples are valid history.
--   * Index on captured_at to support time-windowed audit scans.

CREATE TABLE IF NOT EXISTS prompt_audit (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at             TEXT    NOT NULL,
    league_id               TEXT    NOT NULL,
    season                  INTEGER NOT NULL,
    week_index              INTEGER NOT NULL,
    attempt                 INTEGER NOT NULL,
    angles_summary_json     TEXT    NOT NULL,
    budgeted_summary_json   TEXT    NOT NULL,
    narrative_angles_text   TEXT    NOT NULL,
    narrative_draft         TEXT    NOT NULL,
    verification_passed     INTEGER NOT NULL,
    verification_result_json TEXT   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prompt_audit_captured_at
    ON prompt_audit (captured_at);

CREATE INDEX IF NOT EXISTS idx_prompt_audit_league_week
    ON prompt_audit (league_id, season, week_index);
