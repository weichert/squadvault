-- 002_add_updated_at_to_recap_runs.sql
ALTER TABLE recap_runs ADD COLUMN updated_at TEXT;

-- backfill for existing rows
UPDATE recap_runs
SET updated_at = created_at
WHERE updated_at IS NULL;
