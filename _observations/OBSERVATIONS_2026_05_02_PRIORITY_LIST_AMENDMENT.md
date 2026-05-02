# OBSERVATIONS_2026_05_02 — Priority list amendment

**Predecessor:** `_observations/PRIORITY_LIST_2026_04_28.md`

**Stated purpose:** amend in place by appending. The source memo is preserved as written so its drift is itself part of the record. This memo records the corrected status of every open item on the priority list as of HEAD `696fe8f` on 2026-05-02.

## Status corrections since 2026-04-28

### E1 — DEMOTED to CLOSED

- Previous status: OPEN (priority list, 2026-04-28).
- Current status: CLOSED.
- Closing commit: `a91fc72` — "Verifier Category 7: PLAYER_FRANCHISE attribution check," 2026-04-15.
- Behavior verified at HEAD: PLAYER_FRANCHISE category emits at `src/squadvault/core/recaps/verification/recap_verifier_v1.py:2809`; documented as Category 7 in the file's category-list docstring at line 16.
- Drift severity: 13 days between commit and memo.

### E2 — DEMOTED to CLOSED

- Previous status: OPEN (priority list, 2026-04-28).
- Current status: CLOSED.
- Closing commit: `9271e20` — "Verification V2 complete: cross-week consistency check for streaks and series records," 2026-04-01.
- Behavior verified at HEAD: CONSISTENCY category emits at three sites in the verifier (lines 2262, 2299, 2314); commit added 202 lines to the verifier and 107 lines of test coverage.
- Drift severity: 27 days between commit and memo. The largest drift in this amendment.

### H7 Cat A — DEMOTED to CLOSED

- Previous status: OPEN (priority list, 2026-04-28; H7 dependency).
- Current status: CLOSED.
- Closing commit: H1+H4 closure (`bfee780`), per `OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md`.
- Behavior verified at HEAD: Step 0 of this session ran `prove_ci.sh` directly. The script halted with a visible `❌ Downstream reads from memory_events are not allowed` message rather than a silent rc=1. `set -euo pipefail` is doing its job.

## Items unchanged

| Item | Status | Notes |
|---|---|---|
| H7 Cat B | OPEN | 4 ingest sites flagged at HEAD: `src/squadvault/ingest/_run_matchup_results.py:115`, `src/squadvault/ingest/_run_player_scores.py:99`, `src/squadvault/mfl/_run_historical_ingest.py:262, 272`. Subject of this session's Step 2. |
| H2b | OPEN | `ruff check Tests/` reports 23 errors at HEAD. Forward-looking note: 10 of 23 are autofixable via `--unsafe-fixes`; the H2b brief writer should weigh that option. |
| `d['raw_mfl']` write | OPEN | Now at `src/squadvault/core/recaps/facts/extract_recap_facts_v1.py:187` (was 190 in the brief; 3-line drift). Embedded comment at line 182 — "stash written below is retained pending scope" — confirms deferral discipline is intact. |
| `scripts/diagnose_season_readiness.py:203` latent caller | OPEN | File exists. Line position not re-verified this session. |
| Q1/Q2/Q3 open questions, Item 4b, W7 reception window | OPEN | No evidence available to update. W7 reception window closes ~2026-05-05; addendum is its own short session. |

## Path corrections

The brief and the priority list reference the verifier file as `src/squadvault/recaps/recap_verifier_v1.py`. The actual canonical path at HEAD is `src/squadvault/core/recaps/verification/recap_verifier_v1.py` — note the `core/` segment and the `verification/` subdirectory. Future briefs should use the canonical path.

## The drift pattern

This is the **third** instance of stale-brief-causes-false-start:

1. The `prompt_text` column work — already complete in migration 0009 when a session brief proposed it as new.
2. The Player Trend Detectors T1 phase — firings already verified in production when a night session attempted to start them as new.
3. This amendment — E1 and E2 carried as open on a priority list when both had been shipped (E2 nearly a month before memo write).

The pattern is structural, not a content failure. "Current state" descriptions of an actively-changing repo are inherently fragile — only commits, gate tests, and the working tree itself are durable. Briefs and memos describing repo state become stale as a normal consequence of progress.

The structural fix is not "write better memos." It is **verify before execute, every session.** The norms going forward, applied without exception:

1. **Re-grounding is session step 1, every session.** Until the priority list is rewritten as a generated artifact (commit-aware, not human-curated), it cannot be the authoritative source of "what's open." The repo is.
2. **Cite verifiable evidence per claim.** Every "X is closed" claim in a future brief must include a commit hash. Every "X is open" claim must include a runnable check. No claims of repo state without a path to verify.
3. **Stale-brief signal-out.** A fourth instance is no longer "amend in place." A fourth instance is the signal to redesign the priority-list mechanism — generate it from commit metadata, or retire the format. Three is a pattern; four is a structural problem.

## Cross-references

A future re-grounding pass should also consult:

- `_observations/PRIORITY_LIST_2026_04_28.md` — the source memo this amendment patches.
- `_observations/OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md` — the H7 Cat A closure record.
- `_observations/OBSERVATIONS_2026_04_29_H2_RUFF_AUTOFIX.md` — the H2 ruff autofix predecessor.
- `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — Track A first-distribution context.
- The session brief used to drive this amendment — held in conversation context, not committed to the repo.

## Append-only

This memo amends the priority list by appending. `PRIORITY_LIST_2026_04_28.md` itself is not edited; the source memo's drift is itself a finding worth preserving as written.
