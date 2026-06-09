# Observations - Charter adoption + Unit E1.1 (ruff cleanup)

**Date:** 2026-06-09
**Session:** Shakedown - first Claude Code session under Working Process Charter v1.0
**HEAD at authoring:** `0dfebbd`
**Commit series:**
- `d119e6e` - charter adoption (CLAUDE.md + repo-root allowlist test)
- `c5a3c6c` - STATE.md ledger + Map v1.7 addendum + top-level docs allowlist test
- `bf0833e` - E1.1: ruff errors cleared; ruff pinned
- `0dfebbd` - STATE.md: E1.1 discharged

---

## What shipped

1. **Charter v1.0 adopted.** CLAUDE.md committed and registered in
   `Tests/test_repo_root_allowlist_v1.py` (ALLOWED_ROOT_FILES grew by exactly one).

2. **State ledger created.** `docs/STATE.md` (41 lines, under the ~80 cap) per Charter
   section 4: HEAD meaning, open units by ID, discharged items with hashes, hazards.
   Registered via dated addendum `docs/map_patch_2026_06_09_state_ledger.md` to satisfy
   the docs Map registration gate, and added (with the addendum) to
   `_GRANDFATHERED_TOP_LEVEL_DOCS` in `Tests/test_docs_map_registration_gate_v1.py`.

3. **Unit E1.1 - ruff clean.** `ruff check src/squadvault/` now returns zero.

## Findings

- **The three E402s are legitimate late imports, not violations.**
  `src/squadvault/consumers/rivalry_chronicle_generate_v1.py` calls `load_dotenv()`
  (lines 17-18) *before* importing chronicle-generation modules, so `ANTHROPIC_API_KEY`
  reaches the creative layer at import time. Reordering would defeat that. The fix is a
  per-file-ignore for E402, matching the file's pyproject siblings (the ingest `_run_*`
  modules and `input_contract_v1.py`, which it imports). The other 7 errors (UP037,
  E401, I001 x2, F401 unused `generate_rivalry_chronicle_multi_season_v1`) were genuine
  and autofixed.

- **ruff is unpinned in CI.** `.github/workflows/ci.yml` line 29 installs a bare `ruff`.
  Pinned `ruff==0.15.10` in `requirements.txt` (installed at line 28, before the bare
  install, so the pin holds). This makes lint deterministic *as long as* line 29's bare
  install does not later resolve a different version against an empty cache. A follow-up
  to pin ruff directly in ci.yml line 29 would close the residual gap; left OUT OF SCOPE
  here (would touch CI config beyond the brief). Recorded as a hazard in STATE.md.

## Discrepancy flagged to founder (Charter section 3.4)

The brief labeled discharged item `a5d27dd` as "Cavallini rename." Git shows `a5d27dd`
is "A2 anchor test rename verified closed." The Cavallini/Mahomes anchor revocation
itself is `e5fbb94` (memo) + `97498fa` (purge). The hash is valid and is a real
discharged closure; only the label was loose. STATE.md records git's actual subject
line. No work was blocked.

## Process note

Commit 2 initially shipped a red suite: `test_no_unregistered_top_level_docs_files`
maintains its own allowlist separate from the pre-commit gate (which only checks for a
Map touch). The full suite caught it; the allowlist registration was folded into Commit
2 via amend (unpushed) so each commit lands green. Lesson: the docs Map gate and the
docs-allowlist *test* are two distinct registration surfaces - a new top-level docs file
must satisfy both.
