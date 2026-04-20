# Renderer `render_recap_text_from_facts_v1` dormancy pass

**Date:** 2026-04-20
**Scope:** Read-only investigation. No `src/` or `Tests/` changes, no
DB mutations, no ingest runs. Deliverable is the classification of
one module against three hypotheses (DORMANT / LIVE BUT INDIRECT /
PARITY-SHADOW), following the Item 4 scoping pause on 2026-04-20
that surfaced the dormancy question mid-session and reshaped the
shape-normalization design space enough to warrant its own pass.
**HEAD at observation-time:** `1d800a9` — Phase 10 housekeeping:
promote four tracked diagnostic scripts.
**Follows:** 2026-04-20 Item 4 scoping (paused pending this memo).

---

## Headline finding

`src/squadvault/core/recaps/render/render_recap_text_from_facts_v1.py`
is **DORMANT (post-consumer-retirement orphan)**. Classification is
definitive. The module was last live on or before 2026-03-25; its
sole production consumer was deliberately retired on 2026-03-26 in
commit `0638c9e` as part of a four-consumer cleanup tied to the
legacy `recaps` table deprecation; a partial follow-up in commit
`191f8a7` on 2026-03-31 removed the now-orphaned file-loading wrapper
function but left the rest of the module intact. The module has been
orphaned for 24 calendar days as of HEAD `1d800a9`.

This reshapes Item 4's design space: the
`_extract_waiver_bid_awarded_fields` isinstance-check bug at
`src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:274-280`
silently drops every WAIVER_BID_AWARDED event's add/drop player IDs
from the extractor's normalized output — but nothing in production
currently consumes that normalized output. The bug is real and
latent; it has **zero observable impact on production recaps at
HEAD**. The live renderer is `deterministic_bullets_v1.py`, which
reads `payload.player_id` directly and is unrelated to this module.

---

## Evidence chain

### Step 1 — full import sweep in `src/`

```
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:65
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:184
```

Both hits are non-executable: a docstring mention (line 65) and an
inline comment (line 184). Zero `import` statements, zero `from …
import …` lines, zero dynamic-dispatch patterns. No live importer
of the module anywhere in production code.

### Step 2 — archive-aware sweep

Four archive-shaped directories on disk:

```
scripts/_archive         → 0 hits
scripts/_graveyard       → 0 hits
scripts/_retired         → 0 hits
src/squadvault/_retired  → 0 hits
```

No historical archival trace. Combined with step 5 below, this
confirms the retirement was executed via `git rm` rather than
move-to-archive — consistent with the repo's mixed disposition
pattern where some retirements are archived (e.g., Notion package
to `src/squadvault/_retired/`) and some are simply deleted.

### Step 3 — scripts / ops / consumers / recaps sweep

```
scripts/ (non-archive)      37 .py files  →  0 hits
src/squadvault/ops/          4 .py files  →  0 hits
src/squadvault/consumers/   22 .py files  →  0 hits
src/squadvault/recaps/      15 .py files  →  0 hits
```

Note: `src/squadvault/recaps/` is the top-level sibling to
`src/squadvault/core/recaps/` (different tree, not a subset of what
step 1 already swept). Both trees covered. All four target
directories meaningfully populated — zero hits is substantive, not
vacuous.

### Step 4 — test-coverage classification

Two test files exist and are active against the renderer:

- `Tests/test_render_from_facts_v1.py` (265 lines)
- `Tests/test_render_recap_text_from_facts_v1.py` (216 lines)

`pyproject.toml` declares `testpaths = ["Tests"]`; a
`Tests/conftest.py` is present; neither test file contains
`skip`, `xfail`, `skipif`, or `pytest.mark.*` decorators. Both
contribute to the current 1857-passing baseline.

The tests feed inputs in the exact shape the renderer expects
(`add_player_ids` as `list[str]`, `add_player_ids=["16207"]` for
WAIVER_BID_AWARDED, etc.), so the tests pass regardless of whether
the renderer would function correctly against the actual output of
the production `waiver_bids.py` ingester (CSV string). Test
coverage exercises the renderer's happy path in isolation from any
integration with its former consumer's ingest contract.

The two files are the only `src/`-boundary-crossing importers. No
plugin hook, conftest fixture, parametrize pattern, or
`importlib`-style indirection routes live code through the renderer.

### Step 5 — git history

**5a.** `git log --oneline --all` on the renderer file returns 8
commits. The significant one is `191f8a7` (2026-03-31):

```
Remove 3 dead functions: get_logger, render_recap_from_enriched_path_v1, export_latest_approved_rivalry_chronicle_v1
```

The 8-line diff on the renderer:

```python
-def render_recap_from_enriched_path_v1(path: str, *, db_path: Optional[str] = None) -> str:
-    """Load enriched artifact JSON from path and render recap."""
-    with open(path, "r", encoding="utf-8") as f:
-        artifact = json.load(f)
-    return render_recap_from_facts_v1(artifact, db_path=db_path)
```

This was a thin file-loading wrapper around
`render_recap_from_facts_v1`. The author recognized it as dead and
removed it, but stopped there — `render_recap_from_facts_v1` itself
and all its helpers were not removed.

**5b.** `git log --diff-filter=D -- src/squadvault/` returns 6
commits with src/ deletions. Cross-checking each deleted file's
pre-deletion content for references to the renderer:

```
0638c9e: src/squadvault/consumers/recap_week_render_facts.py (1 hit)
```

Commit `0638c9e` (2026-03-26), "Remove EAL fallback dead code,
retire 4 legacy consumers, clean recap_week_render," deleted 47
lines that contained exactly one reference to the renderer. This
was the sole production caller.

The deleted consumer (reconstructed from `git show`):

```python
from squadvault.core.recaps.render.render_recap_text_from_facts_v1 import render_recap_from_enriched_path_v1

def _get_active_artifact_path(db_path, league_id, season, week_index):
    """Read artifact_path from legacy recaps table (deprecated, local copy)."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT artifact_path FROM recaps
               WHERE league_id=? AND season=? AND week_index=? AND status='ACTIVE'
               ORDER BY recap_version DESC LIMIT 1""",
            ...
        ).fetchone()
```

The consumer read `SELECT artifact_path FROM recaps` — the legacy
`recaps` table that was itself retired. Once the table was retired,
the consumer was dead; the consumer was the renderer's sole call
site via the path-wrapper; the path-wrapper was removed 5 days
later in `191f8a7`; the rest of the module was overlooked.

### Step 6 — stale comments at `extract_recap_facts_v1.py:65` and `:184`

Both comments accurately describe the renderer's actual behavior
(it reads `d["raw_mfl"]["type"]` for transaction-type dispatch).
They were correct when authored. Lines 67-69 contain load-bearing
documentary justification:

> Post-promotion events do not strictly require this parse for
> field extraction, but the render stash contract requires the
> parsed dict remain available.

This sentence currently preserves a behavior contract with no
consumer. A quick downstream check of `d["raw_mfl"]` live readers
surfaces an incidental follow-on:

```
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:64  (comment)
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:185  (comment)
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:190  (write site)
```

The `d["raw_mfl"] = raw` write at line 190 has **zero live readers**.
The stash itself is currently writing to a field no live consumer
reads. This is a retirement-session follow-on, not part of today's
classification.

### Additional finding — architecture gate baseline

Full-repo `git grep` surfaced a seventh reference:
`Tests/test_architecture_gates_v1.py:210`. The
`test_core_broad_exception_count` gate sets a baseline of `<=8`
broad exception handlers across `src/squadvault/core/` and
documents the breakdown inline:

> 2 in canonicalize (ROLLBACK guard), 2 in deterministic_bullets
> (resolver fallback), 2 in render_recap_text_from_facts (str
> fallback + bullet enrichment guard).

If the module is retired, 2 of those 8 handlers vanish; the gate
test's baseline becomes loose (`<=8` allowing 6 remaining) and the
inline documentary breakdown becomes stale. Retirement work must
lower the baseline to `<=6` in the same commit and update the
comment. Not a classification input, but a direct implication for
the retirement-session PR shape.

---

## Classification

**DORMANT (post-consumer-retirement orphan).**

Not PARITY/SHADOW:
- No module-level docstring frames the module as an alternative or
  differential renderer.
- No commit body in the file's 8-commit history names a parity or
  shadow purpose.
- Subsequent touches (`d4df2af` Implementation Excellence Plan,
  `26b53b0` Code quality v2) applied type modernization and fixture
  immutability uniformly, treating the file as normal live code.
  There is no indication any maintainer was aware of its dormancy
  after `191f8a7`.

Not LIVE BUT INDIRECT:
- No `importlib`, `getattr(module, name)()`, or dynamic dispatch in
  production code.
- No ops/scripts entry point.
- Test files import directly; they are the only external importers.

The commit trail is consistent with a clean-retirement-in-progress
that stalled. `0638c9e` retired the consumer; `191f8a7` cleaned
the obvious orphan wrapper; no third commit completed the job.

---

## Recommended next step

Retirement, as a dedicated session, in a single-topic commit. Work
items for that session (not this one):

1. Move `src/squadvault/core/recaps/render/render_recap_text_from_facts_v1.py`
   to `src/squadvault/_retired/`, matching the Notion package
   retirement pattern.
2. Delete `Tests/test_render_from_facts_v1.py` and
   `Tests/test_render_recap_text_from_facts_v1.py` — 481 lines of
   orphan coverage. Retention would preserve tests for retired
   code, violating the discipline that test surface area maps to
   live surface area.
3. Lower the `test_core_broad_exception_count` gate baseline from
   `<=8` to `<=6` and update the inline breakdown comment at
   `Tests/test_architecture_gates_v1.py:208-210`.
4. Rewrite the two stale comments in `extract_recap_facts_v1.py:65`
   and `:184` to reflect that the raw_mfl parse no longer services
   a render-layer contract. Remove the load-bearing justification
   at lines 67-69.
5. Scope whether the `d["raw_mfl"]` write at
   `extract_recap_facts_v1.py:190` should also be retired —
   currently has zero live readers. Worth treating as its own
   scoping question rather than folding into the retirement commit,
   because removing the write risks per-type dispatch churn in
   `extract_recap_facts_v1.py` that should be reasoned about
   separately from module retirement.

### Implication for Item 4

With the dormant renderer confirmed, the two-axis divergence
between `transactions.py` and `waiver_bids.py` that was the core
of Item 4's scoping has **no observable impact on production
recaps today**. The consumer bug in
`_extract_waiver_bid_awarded_fields` (lines 274-280) produces
empty-player-id output that the live renderer
(`deterministic_bullets_v1.py`) never reads — it reads
`payload.player_id` from the canonical event directly.

Item 4b (shape-normalization fix) moves from "bug with impact" to
"latent correctness gap in a dormant contract." Right sequencing:

- (a) Retire the dormant renderer first (its own session, per
  recommended next step above).
- (b) Re-scope Item 4 against the post-retirement codebase. The
  fix may shrink substantially if the `d["raw_mfl"]` write also
  goes away, since the chain of consumers of
  `_extract_waiver_bid_awarded_fields`'s normalized output becomes
  empty rather than `{renderer, raw_mfl stash}`.

The sibling `_extract_free_agent_fields` isinstance-check pattern
at lines 303-309 is equally inert today (FREE_AGENT flows from
`transactions.py` which emits lists, so the isinstance check
always matches) but should be included in any eventual shape-
normalization pass for consistency.

---

## Out of scope

- Any code change to the renderer module. Retirement is its own
  commit in its own session, conditional on approval of this memo's
  recommendation.
- Any fix to the `_extract_waiver_bid_awarded_fields` or
  `_extract_free_agent_fields` isinstance-check patterns
  (Item 4b — re-scoping deferred until post-retirement).
- Cleanup of the stale comments in `extract_recap_facts_v1.py:65`,
  `:184`, and the orphaned `d["raw_mfl"]` write at line 190 —
  retirement-session follow-ons.
- Disposition of the 481 lines of orphan test coverage — handled
  as part of the retirement commit.
- Architecture-gate baseline adjustment at
  `test_architecture_gates_v1.py:211` — retirement commit.
- Thread-1 ruff `Tests/` cleanup (238 errors; its own session).
- Row 25 diagnostic, Q5 pass-rate re-examination, row 17a1 retest.

---

## Cross-references

- **userMemories recent_updates** — "Item 4 … partially scoped
  2026-04-20 … `render_recap_text_from_facts_v1.py` appears
  DORMANT (zero src/ imports); live renderer is
  `deterministic_bullets_v1.py` reading `payload.player_id`.
  Confirm dormancy before proceeding." This memo confirms.
- **Commit `0638c9e`** (2026-03-26) — "Remove EAL fallback dead
  code, retire 4 legacy consumers, clean recap_week_render."
  Deleted the sole production caller of this module.
- **Commit `191f8a7`** (2026-03-31) — "Remove 3 dead functions."
  Partial dormancy recognition; removed the file-loading wrapper
  but not the rest of the module.
- **Session brief** — "Item 4 Dormancy Pass." This memo is that
  session's deliverable.
