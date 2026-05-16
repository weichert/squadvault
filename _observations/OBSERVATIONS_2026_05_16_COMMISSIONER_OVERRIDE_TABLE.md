# Phase 11 -- Commissioner Display Override Table

**Date:** 2026-05-16
**Status:** Closed. Schema applied, helper shipped, tests passing.

---

## 1. Rationale

Facts are immutable and append-only. Human circumstances sometimes require
controlling how history is presented -- a death, a bitter departure, a name
dispute. The override system governs the display layer without touching the
substrate.

Core distinction: facts are immutable. Presentation is governed.

---

## 2. Schema -- franchise_display_overrides

Applied to both .local_squadvault.sqlite and fixtures/ci_squadvault.sqlite.
Also added to src/squadvault/core/storage/schema.sql (schema drift gate).

| Column | Type | Purpose |
|---|---|---|
| league_id | TEXT | League identifier |
| franchise_id | TEXT | Franchise slot |
| season_from | INTEGER NULL | Start of override window (NULL = open) |
| season_to | INTEGER NULL | End of override window (NULL = open) |
| display_name_override | TEXT NULL | Show this name instead of MFL name |
| suppressed | BOOLEAN | Hide from surfaces; show "Former Member" |
| memorial_flag | BOOLEAN | Present as tribute |
| narrative_excluded | BOOLEAN | AI narrative skips this franchise |
| override_reason | TEXT | Human-readable justification |
| set_by | TEXT | Commissioner username or "admin" |
| set_at | TIMESTAMP | When the override was set |

UNIQUE constraint on (league_id, franchise_id, season_from, season_to).

---

## 3. What the override system must NEVER do

- Delete canonical events
- Change scores, outcomes, or matchup results
- Backfill or fabricate events
- Alter the append-only ledger in any way

The override table is itself an immutable append-only record.

---

## 4. Helper module

`src/squadvault/core/recaps/context/franchise_display_overrides_v1.py`

Two public functions:

**get_franchise_display_name(db_path, league_id, franchise_id, season) -> str**

Resolution order:
1. Check franchise_display_overrides for an active override
   (season_from <= season <= season_to, NULL bounds are open).
   - If display_name_override is set: return it.
   - If suppressed=1: return "Former Member".
2. Fall back to franchise_directory for the given season.
3. Fall back to raw franchise_id if not found.

**is_narrative_excluded(db_path, league_id, franchise_id, season) -> bool**

Returns True if narrative_excluded=1 or suppressed=1 on an active override.

---

## 5. Commissioner SQL pattern

```sql
-- Suppress a departed member from display for their tenure
INSERT INTO franchise_display_overrides
  (league_id, franchise_id, season_from, season_to, suppressed,
   override_reason, set_by)
VALUES
  ('70985', '0010', 2018, 2022, 1,
   'Neal and Baber no longer in league', 'weichert');

-- Memorial flag for a deceased member
INSERT INTO franchise_display_overrides
  (league_id, franchise_id, season_from, season_to, memorial_flag,
   display_name_override, override_reason, set_by)
VALUES
  ('70985', '0007', 2010, 2025, 1,
   'In memory of [name]', 'Founding member, passed 2025', 'weichert');

-- Name override for a sensitive departure
INSERT INTO franchise_display_overrides
  (league_id, franchise_id, season_from, season_to, display_name_override,
   narrative_excluded, override_reason, set_by)
VALUES
  ('70985', '0010', 2018, 2020, 'Former Member', 1,
   'Amicable departure', 'weichert');
```

---

## 6. Tests

`Tests/test_franchise_display_overrides_v1.py` -- 13 tests covering:
- display_name_override returned when active
- Override not active outside season range
- suppressed returns "Former Member"
- suppressed outside range falls back normally
- Open-ended override (season_to=NULL)
- NULL both bounds applies to all seasons
- display_name_override takes precedence over suppressed
- Fallback to raw franchise_id when not in directory
- is_narrative_excluded: no override returns False
- narrative_excluded flag returns True
- suppressed implies narrative_excluded
- narrative_excluded not active outside range

---

## 7. Display layer threading

The helper is available for any display surface to call. No existing
display surfaces have been wired to it in this session -- that is
incremental work as each surface is built out. The helper is the
single choke-point; surfaces call it instead of querying
franchise_directory directly.

---

## 8. Files changed

- `src/squadvault/core/storage/schema.sql` -- franchise_display_overrides table added
- `src/squadvault/core/recaps/context/franchise_display_overrides_v1.py` -- new helper module
- `Tests/test_franchise_display_overrides_v1.py` -- 13 tests (all passing)
- `Tests/recaps/writing_room/test_prompt_audit_v1.py` -- registered in _NON_EMITTING_CONTEXT_MODULES
- `.local_squadvault.sqlite` -- table applied (not committed; local DB)
- `fixtures/ci_squadvault.sqlite` -- table applied
