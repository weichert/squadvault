# Observations — H1+H4 shipped; memory_events gate exposed (2026-04-29)

## Summary

H1 (Finding B mechanism closure: `set -euo pipefail` to
`scripts/prove_ci.sh`) and H4 (retire dangling `_status.sh` source
from `scripts/recap`) shipped together at commit `bfee780`,
2026-04-29 ~01:00 ET. Coupled because H1's strict-mode addition
surfaced H4 as a silent-rc=1 latent failure on its first attempted
solo apply — exactly the failure mode H1 was designed to expose.

H1's strict mode also surfaced a second latent failure that was
not in scope for this session and is now blocking
`prove_ci.sh` from returning rc=0 cleanly: the
`scripts/check_no_memory_reads.sh` gate has been silently red since
the Implementation Excellence Plan (`d4df2af`) moved
`run_ingest_then_canonicalize.py` from `src/squadvault/core/canonicalize/`
to `src/squadvault/ops/` without updating the allowlist. The session
brief carries this as a known standing item ("6× memory_events
allowlist violations (downstream-read gate)") but the relationship
between the two — that errexit promotion would expose it — was not
recognized in the closure memo.

This memo records what shipped, what was exposed, and what to do
about it.

## What shipped

Commit `bfee780` on `origin/main`:

- `scripts/prove_ci.sh` (+8 lines): added a `STRICT EXECUTION
  (Finding B closure)` block immediately after the deterministic
  envelope, containing `set -euo pipefail` and a comment explaining
  why it is now safe to land. File mode also changed from 644 to
  755 to match every other `prove_*.sh` in the repo.
- `scripts/recap` (-3 lines): removed the dangling `source
  "$SCRIPT_DIR/_status.sh"` line. The shared status helper was
  archived to `scripts/_archive/unreferenced/_status.sh` on
  2026-03-11 (commit `2dfb96e`); no active script in the repo uses
  the `sv_*` functions it defined. The source line was pure dead
  code that had been silently failing for ~7 weeks, masked by the
  absence of errexit.

## How the bundling decision was made

H1 was applied solo first per the original plan. Validation produced
`rc=1` with **0** ERROR-prefixed lines and the diagnostic line:

```
/Users/.../scripts/recap: line 5: scripts/_status.sh: No such file or directory
```

This is the canonical signature of the silent-rc=1 case errexit is
designed to expose. Because the failing gate is the "Gate: CWD
independence (shims) v1" gate, which had been passing under errexit-off
despite the source failure, H4 (already on the priority list as a
standalone item) was a mechanically-coupled prerequisite for H1's
clean validation. Bundling them produced a single coherent commit.

## What H1 also exposed (out of scope for this session)

After commit, post-commit `prove_ci.sh` returned `rc=1` again,
halting at:

```
=== Check: no forbidden downstream reads from memory_events ===
src/squadvault/ingest/_run_matchup_results.py:115
src/squadvault/ingest/_run_player_scores.py:99
src/squadvault/ops/run_ingest_then_canonicalize.py:37
src/squadvault/ops/run_ingest_then_canonicalize.py:60
src/squadvault/mfl/_run_historical_ingest.py:262
src/squadvault/mfl/_run_historical_ingest.py:272
❌ Downstream reads from memory_events are not allowed (outside allowlist)
```

This gate has been silently red since at least the Implementation
Excellence Plan work at `d4df2af`. The 6 violations split into two
categories:

### Category A — file moved, allowlist not updated (2 of 6 hits)

`src/squadvault/ops/run_ingest_then_canonicalize.py` — same file as
the allowlist's `src/squadvault/core/canonicalize/run_ingest_then_canonicalize.py`,
which was deleted at `d4df2af`. The active path is `ops/`. The
allowlist still references the deleted `core/canonicalize/` path.

**This is straightforward to resolve** — update the allowlist entry
to point at the current location. ~5 minute fix.

### Category B — ingest re-entrancy checks (4 of 6 hits)

- `src/squadvault/ingest/_run_matchup_results.py:115` — `SELECT
  COUNT(*) FROM memory_events WHERE event_type = 'WEEKLY_MATCHUP_RESULT' ...`
- `src/squadvault/ingest/_run_player_scores.py:99` — `SELECT
  COUNT(*) FROM memory_events WHERE event_type = 'WEEKLY_PLAYER_SCORE' ...`
- `src/squadvault/mfl/_run_historical_ingest.py:262` — `SELECT
  COUNT(*) FROM memory_events WHERE league_id = ?`
- `src/squadvault/mfl/_run_historical_ingest.py:272` — `SELECT
  DISTINCT season FROM memory_events WHERE league_id = ? ORDER BY season`

These are all idempotency / re-entrancy checks during ingest itself
("did we already ingest this league/season?"). They are not
downstream consumer reads of `memory_events` for narrative-layer
use. The gate's stated scope ("no forbidden **downstream** reads")
suggests these were never meant to be caught — but the allowlist
is empty for the ingest path, and the gate's grep matches any
`FROM memory_events`.

**Two possible resolutions, choice deferred to a future session:**

1. **Expand the allowlist.** Add the four ingest paths. Treats them
   as legitimate ingest-layer re-entrancy reads. Lowest-effort.
2. **Refactor to use a different signal.** If ingest re-entrancy
   should not depend on `memory_events` reads (e.g., should use a
   `_schema_migrations`-style state table or a checkpoint mechanism),
   the four sites need code changes. Higher-effort.

The decision between (1) and (2) requires reading the architectural
intent of the original gate creation (commits `41e5127` "Ops:
enforce no-memory-reads via explicit allowlist" and `4bc8d09` "Ops:
allowlist canonicalize authority readers in no-memory-reads check")
and the surrounding ingest design. Not a 1 AM decision.

## Current state

- HEAD `bfee780` is on `origin/main`. H1 and H4 are shipped.
- `prove_ci.sh` returns `rc=1` because the memory_events gate halts
  execution under errexit. The pre-commit hook (banner, no-xtrace,
  repo-root allowlist) is unaffected and continues to pass.
- All work in `src/squadvault/core/` continues to function. Tests
  continue to pass. No production behavior changed; a previously-
  silent gate is now a loud one.

This is **architecturally correct** — surfacing latent failures is
the entire point of `set -e`. The cost is that "running
`prove_ci.sh` to a clean rc=0" is no longer the default state until
the memory_events gate is resolved. Until then, that single gate is
the canonical "first item that needs attention before the rest of
prove_ci runs."

## Priority list update needed

`_observations/PRIORITY_LIST_2026_04_28.md` should be amended (in a
future session) to:

- Mark **H1** CLOSED.
- Mark **H4** CLOSED.
- Promote **memory_events allowlist resolution** from "Standing
  items (out of scope)" to a new **H7** entry, scoped as Category A
  (5 min) + Category B decision (research required) + apply.
- Update the listed Tests/ ruff error count from 229 → whatever it
  is at that point.

The amendment is a 30-minute pure-docs task, akin to H3 (F-series
finding memo amendment).

## Findings

### F1 — Closure memo's "now safe to land" assessment was incomplete

`OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md` asserted that "all
pre-existing silent-rc=1 gates have been retired." Two were not:

- The CWD-independence gate (silent-rc=1 from missing `_status.sh`,
  closed by H4 in this commit).
- The memory_events allowlist gate (silent-rc=1 from stale allowlist
  + ambiguous "downstream" scope, still open).

Lesson: the closure memo's verification methodology — running
`prove_ci.sh` pre-edit and counting ERROR-prefixed lines — does not
distinguish between "no failures" and "failures that produce output
in non-ERROR-prefixed format." The CWD-independence gate failed
with a `bash: source: No such file or directory` line; the
memory_events gate failed with a `❌` line. Neither matches the
`^ERROR|ERROR:` regex. A future "is prove_ci really clean?" check
should also examine the script's actual rc, not just the ERROR
line count.

This is not a critique of the closure memo — verification under
errexit-off is fundamentally limited because the script can return
rc=0 even when individual gates have failed. The honest assessment
of "truly clean" required H1 itself.

### F2 — The session brief carried the memory_events item but missed the H1 connection

The session brief explicitly listed "6× `memory_events` allowlist
violations (downstream-read gate)" as a standing item out of scope
for the H1 session. The brief did not flag that H1's strict mode
would *promote* this standing item from "silent" to "blocking
prove_ci rc=0." With hindsight, the priority list memo should have
flagged this dependency in H1's "what to expect after." It did not.

Lesson: when adding errexit to a script that runs other gates, the
authoring step should enumerate every existing silent-rc=1 gate and
flag which ones will become blocking. The check is mechanical:
`grep "exit 1" gate scripts; check for `❌` and `bash: ... not
found` patterns in current pre-edit output`.

### F3 — Mode change on prove_ci.sh (644 → 755) is a positive side-effect

The apply script chmod'd `prove_ci.sh` to 755 to match every other
`prove_*.sh` in the repo. The pre-edit mode of 644 was an oversight;
the script was always run via `bash scripts/prove_ci.sh`, so
non-executable mode was never a functional issue, but it diverged
from the convention. The chmod corrected this.

## Cross-references

- Commit `bfee780` — H1+H4 ship.
- Commit `9bbd374` — pre-H1 cleanup of untracked archive script.
- Commit `2dfb96e` (2026-03-11) — original `_status.sh` deletion.
- Commit `d4df2af` — `run_ingest_then_canonicalize.py` move.
- Commit `41e5127` — original creation of the no-memory-reads gate.
- `OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md` — original
  F-series triage.
- `OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md` — closure (now
  partially superseded by F1 in this memo).
- `_observations/PRIORITY_LIST_2026_04_28.md` — items H1 (CLOSED),
  H4 (CLOSED), and memory_events (promoted to H7, pending).
