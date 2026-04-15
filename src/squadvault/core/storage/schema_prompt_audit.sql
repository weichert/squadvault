-- SquadVault Prompt Audit sidecar schema (v2)
--
-- Purpose: Append-only capture of prompt attempts emitted by the Writing Room
-- lifecycle (one row per retry attempt inside _generate_draft). This is an
-- observation sidecar, not a fact store — narratives and verification results
-- are derived elsewhere. Rows are immutable by convention and append-only by
-- structure: no UNIQUE constraint, no update path, no delete path from the
-- application layer.
--
-- v2 contract deltas from v1:
--   * No `version` column. The table *is* v1 of the audit surface; schema
--     versioning lives in the schema file name / migration layer, not in row
--     data.
--   * No UNIQUE constraint on (league_id, season, week_index, attempt).
--     Append-only semantics mean duplicate keys are valid history, not
--     integrity violations. The `id` PK alone is sufficient.
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

-- Reverify sidecar (mirror of migration 0008). Append-only
-- re-verification results keyed by prompt_audit.id and verifier_tag.

CREATE TABLE IF NOT EXISTS prompt_audit_reverify (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_audit_id       INTEGER NOT NULL,
    reverified_at         TEXT    NOT NULL,
    verifier_tag          TEXT    NOT NULL,
    passed                INTEGER NOT NULL,
    hard_failure_count    INTEGER NOT NULL,
    soft_failure_count    INTEGER NOT NULL,
    result_json           TEXT    NOT NULL,
    FOREIGN KEY (prompt_audit_id) REFERENCES prompt_audit(id)
);

CREATE INDEX IF NOT EXISTS idx_reverify_source
    ON prompt_audit_reverify (prompt_audit_id);

CREATE INDEX IF NOT EXISTS idx_reverify_tag
    ON prompt_audit_reverify (verifier_tag);
