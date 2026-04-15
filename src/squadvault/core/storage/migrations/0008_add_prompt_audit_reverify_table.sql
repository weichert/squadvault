-- Migration 0008: prompt_audit_reverify observation sidecar table.
--
-- Append-only re-verification results produced by
-- scripts/reverify_prompt_audit.py. Each row captures a single
-- prompt_audit draft re-run through the current recap_verifier_v1
-- code and tagged with a verifier_tag (typically a commit short-SHA)
-- so results from different verifier versions can coexist and be
-- compared.
--
-- Observation sidecar — never feeds back into facts, never alters
-- drafts, never gates publication. The only consumer is the delta
-- summary printed by the reverify script, used as a merge gate for
-- verifier code changes.
--
-- Contract:
--   * Append-only: no UPDATE, no DELETE from the application layer.
--   * No UNIQUE constraint — re-running the same tag is valid history.
--   * Foreign key on prompt_audit.id for referential integrity.
--   * Indexes on prompt_audit_id (join performance) and verifier_tag
--     (tag-scoped queries).

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
