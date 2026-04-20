# scripts/audit_queries/

Read-only SQL queries against the `prompt_audit` table (migration 0007).

## What this directory is

A small library of `SELECT`-only queries to observe what the model actually
does inside the Writing Room's `_generate_draft` retry loop. Phase 10 is
**Operational Observation** — these queries exist to look, not to act on
what they find.

Every query in this directory is read-only by construction:

- `SELECT` only — no `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `PRAGMA`
- No new tables, views, or indexes
- No mutation of `prompt_audit` itself (it is append-only by contract)

If a query result genuinely demands a code change, surface it for discussion
before writing code. The discipline is: write the query, look at the result,
resist the urge to act.

## What the table holds

One row per prompt attempt inside `_generate_draft`'s retry loop, written
**after** verification runs. A 3-retry week with a passing 3rd attempt
produces three rows: two with `verification_passed=0` and one with
`verification_passed=1`. The maximum `attempt` per `(season, week_index)`
is therefore the final outcome.

If the model produces no draft at all (API key missing, EAL silence), the
hook is bypassed and no row is written. If verification itself raises an
exception, the loop exits early and again no row is written. The table
contains only attempts the model produced that successfully ran through
the verifier.

### Column reference

| column                    | shape                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------|
| `attempt`                 | 1, 2, 3 — position in the retry loop                                                  |
| `angles_summary_json`     | JSON array `[{"category": "X", "detector": "D##"\|"UNMAPPED"}, …]` — all surfaced     |
| `budgeted_summary_json`   | same shape — only the angles that actually went into the prompt                       |
| `narrative_angles_text`   | the prose-format angle list passed to the model                                       |
| `narrative_draft`         | the model's response                                                                  |
| `verification_passed`     | 0 or 1                                                                                |
| `verification_result_json`| `{"passed": bool, "hard_failures": […], "soft_failures": […], "checks_run": int}`     |

Each entry in `hard_failures` / `soft_failures` has shape
`{"category": "SCORE\|SUPERLATIVE\|STREAK\|SERIES\|BANNED_PHRASE\|PLAYER_SCORE", "severity": "HARD", "claim": "…", "evidence": "…"}`.

Because `_serialize` uses `sort_keys=True`, two attempts with byte-identical
angle sets will have byte-identical `angles_summary_json` strings — angle-set
stability across retries (Q07) is just a string-equality check.

## Populating the table

```bash
source .env.local                # sets ANTHROPIC_API_KEY
export SQUADVAULT_PROMPT_AUDIT=1 # arms the audit hook
./scripts/py scripts/regenerate_season.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 --season 2025 \
    --start-week 1 --end-week 18 \
    --reason "phase10-observation-2025"
```

Without `ANTHROPIC_API_KEY` the hook correctly writes nothing (no draft is
produced, so the loop exits before the audit call). Without
`SQUADVAULT_PROMPT_AUDIT=1` the hook returns immediately as a no-op.

## Running a query

```bash
sqlite3 -header -column .local_squadvault.sqlite < scripts/audit_queries/01_pass_rate_by_attempt.sql
```

Or with separators for CSV-friendly output:

```bash
sqlite3 -separator $'\t' -header .local_squadvault.sqlite < scripts/audit_queries/03_detector_frequency.sql
```

## Query catalog

| file                                              | question                                                              |
|---------------------------------------------------|-----------------------------------------------------------------------|
| `01_pass_rate_by_attempt.sql`                     | Does retry actually help? Pass rate at attempt 1 vs 2 vs 3            |
| `02_attempts_per_week.sql`                        | How often does a week settle on attempt 1 vs needing 2 or 3 retries?  |
| `03_detector_frequency.sql`                       | Which detectors fire most/least often, surfaced vs budgeted           |
| `04_angle_count_vs_pass.sql`                      | Does the model do better with more angles or fewer?                   |
| `05_draft_length_by_outcome.sql`                  | Do passing drafts cluster at a different length than failing ones?    |
| `06_detector_co_occurrence.sql`                   | Which detector pairs show up together inside the same attempt?        |
| `07_angle_set_stability_across_retries.sql`       | Across retries of the same week: angle-set churn or only prose churn? |
| `08_failure_category_frequency.sql`               | Which verifier categories actually fail (SCORE, SUPERLATIVE, etc.)?   |
| `09_unmapped_categories.sql`                      | Drift-detector cross-check: any UNMAPPED categories slipping through? |
| `10_final_outcome_per_week.sql`                   | Per-week rollup: clean / passed-after-retry / exhausted-retries       |
| `11_superlative_failure_prose.sql`                | For each SUPERLATIVE hard_failure: claim, evidence, and prose         |
| `12_tarball_gap_rows_prose.sql`                   | Recover prose for five rows missing from the 04-19 scan tarball       |

## Pairing queries with prose notes

Per the session brief, the deliverable is *queries + plain-prose
observations*. After running each, jot a sentence or two: what did you
expect, what did you see, what (if anything) surprised you. The
surprising ones are the ones worth keeping.

## What NOT to do here

Do not add:

- Aggregation that scores or ranks attempts against each other in a way
  that suggests a "best" detector or a "best" angle count
- Anything that writes back to `prompt_audit` or any other table
- Any view or trigger that ties query output to lifecycle behavior
- Detector-tuning logic, retry-loop tuning logic, or prompt edits
  derived from these queries (those are later-phase decisions, made
  after observation, not during it)

The audit table is observation-only. These queries are observation-only.
That is the whole point.
