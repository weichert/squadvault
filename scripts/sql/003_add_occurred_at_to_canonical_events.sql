ALTER TABLE canonical_events ADD COLUMN occurred_at TEXT;

-- backfill occurred_at from the chosen best_memory_event_id
UPDATE canonical_events
SET occurred_at = (
  SELECT me.occurred_at
  FROM memory_events me
  WHERE me.id = canonical_events.best_memory_event_id
)
WHERE occurred_at IS NULL;
