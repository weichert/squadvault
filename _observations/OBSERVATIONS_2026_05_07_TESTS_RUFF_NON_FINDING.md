# OBSERVATIONS — Tests/ ruff cleanup non-finding (5th instance of stale-backlog hazard)

**Drafted:** 2026-05-07.
**HEAD at run:** `769f80a`.
**Phase:** 10 — Operational Observation.
**Position in plan:** Closure of standing-backlog item carried as "Tests/ ruff cleanup (deferred — 238 errors)" through multiple sessions. Non-finding: actually clean at HEAD.

---

## TL;DR

- `ruff check Tests/` returns `All checks passed!` at HEAD `769f80a`.
- `pyproject.toml` shows Tests/ is **not** in `[tool.ruff].exclude` — the clean is real, not a config dodge.
- Memory edit framing of "238 errors deferred" is stale. Per the OBSERVATIONS_2026_05_02 priority-list amendment, the count was 23 errors (with 10 autofixable) at HEAD `696fe8f`; by the current HEAD all 23 have been resolved through subsequent work.
- This is the **fifth** documented instance of the stale-backlog-item hazard. Per the 2026-05-02 amendment's own discipline note: "Three is a pattern; four is a structural problem." We are at five.
- Standing-backlog item retires. No further work.

---

## 1. Verification

The repo is at HEAD `769f80a` (Tier 5 doctrine session brief, 2026-05-07).

    $ ruff check Tests/
    All checks passed!

    $ ruff check src/ Tests/
    All checks passed!

`pyproject.toml` `[tool.ruff].exclude` lists only `scripts/`, `_archive/`, `_graveyard/`, `_retired/`. Tests/ is in scope. The clean state is genuine.

## 2. The five-instance stale-backlog pattern

Per the OBSERVATIONS_2026_05_02 priority-list amendment §"The drift pattern":

> This is the **third** instance of stale-brief-causes-false-start:
>
> 1. The `prompt_text` column work — already complete in migration 0009 when a session brief proposed it as new.
> 2. The Player Trend Detectors T1 phase — firings already verified in production when a night session attempted to start them as new.
> 3. This amendment — E1 and E2 carried as open on a priority list when both had been shipped (E2 nearly a month before memo write).
>
> [...] A fourth instance is no longer "amend in place." A fourth instance is the signal to redesign the priority-list mechanism — generate it from commit metadata, or retire the format. Three is a pattern; four is a structural problem.

The fourth instance was the SCORE_VERBATIM "59 rows" figure, identified during this session's 2026-05-07 arc (memoed in 16d4a1b §2: actual count 127, not 59 — wrong by more than 2x in memory and three predecessor session briefs).

The fifth instance is this finding: Tests/ ruff cleanup carried as deferred-with-238-errors in current memory through multiple sessions, when reality is clean at HEAD.

The pattern is structural, not content. Memory is a snapshot of when it was last written; the repo is the canonical state. Standing-backlog items that carry numeric counts or specific deferred-state framing are most prone to drift.

## 3. The structural fix the 2026-05-02 amendment proposed

Two proposals from that memo's Norm 1 ("Re-grounding is session step 1, every session"):

(a) Rewrite the priority list as a **generated artifact** — commit-aware, not human-curated. The mechanism would scan recent commits for closed items and emit a current state.

(b) Retire the format. If the priority list cannot be the authoritative source of "what's open," only the repo can.

Neither has shipped. The 2026-05-02 amendment landed at `696fe8f`; subsequent work has continued operating with the same human-curated standing-backlog format. The five-instance pattern is the predictable outcome.

This memo does not ship the structural fix. The memo records the pattern reaching five instances and flags it as overdue. A separate session — likely the next one after Tier 5 doctrine — could scope either of (a) or (b) properly.

## 4. Verdict and standing-backlog update

**Tests/ ruff cleanup retires from the standing backlog.** The item was closed sometime between OBSERVATIONS_2026_05_02 (23 errors at `696fe8f`) and the current HEAD (`769f80a`). The closing commit(s) are not specifically identified in this memo — pinpointing them would require a `git log -p Tests/` walk, which is over-effort for a non-finding closure.

What remains is the meta-pattern question: when does the next stale-backlog item get caught? Per the 2026-05-02 amendment's own framing, every session's Step 0 re-grounding is supposed to catch this. In practice, items that haven't been touched in multiple sessions accumulate stale framing in memory until a session specifically targets them.

The honest framing going forward: **a standing-backlog item's continued presence in memory is not evidence of its current state.** Each item should be re-verified on the session that targets it. The cost of re-verification is cheap (one paste); the cost of acting on stale framing is non-zero.

## 5. Re-activation criterion

The thread closes here, but conditions under which it would re-fire:

- Future commit introduces ruff errors in Tests/ → `ruff check Tests/` becomes non-zero.
- `pyproject.toml` ruff config tightens (e.g., new lint rule selected) and Tests/ has pre-existing violations under the new rule.

Neither is current. The thread is closed.

## 6. Standing-backlog updates

- **Tests/ ruff cleanup:** CLOSED. Non-finding; clean at HEAD.
- **Meta-pattern (priority-list mechanism):** flagged at fifth instance. Named-only as a separate future-session item per the 2026-05-02 amendment's proposed structural fixes (a) generate from commit metadata or (b) retire the format.

Other open items unchanged:

- Tier 5 doctrine session (brief at 769f80a awaiting execution).
- Cat 3c row-76 W14 2025 attribution edge case (deferred).
- Snap-outcome detection (named-only).
- NOTABLE-pass alphabetical lockout investigation (named-only).
- `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` (deferred — to be inspected immediately following this memo per current session plan; line position likely drifted per OBSERVATIONS_2026_05_02's :187 finding).
- Player-streak verb inversion thread (named-only).
- Bug 1 classifier current-week scope extension (named-only, surfaced in Tier 5 brief).

## 7. Files referenced

- `pyproject.toml` — `[tool.ruff].exclude` confirms Tests/ in scope.
- `_observations/OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` — source of the three-instance pattern framing and the proposed structural fixes (a)/(b).
- `_observations/OBSERVATIONS_2026_05_07_SCORE_VERBATIM_STEP_0_PROBE.md` (16d4a1b) — fourth instance (the "59 rows" finding).

---

## 8. Methodology note

The non-finding closure is itself a useful artifact. Without writing this memo, the next session attempting Tests/ ruff cleanup would either: (a) discover the clean state and re-derive this finding mid-session, or (b) attempt fixes that don't apply and waste cycle time before discovery. The memo costs five minutes to write; either alternative costs more.

The same logic supports closure memos for any deferred standing-backlog item that turns out to be already-resolved. The act of *verifying-then-closing* is cheaper than letting the item carry forward indefinitely.

This is consistent with the OBSERVATIONS_2026_05_02 amendment's Norm 1 (re-grounding-is-step-1) and Norm 2 (cite-verifiable-evidence-per-claim). The marginal addition: Norm 3 — *closure memos for non-findings are durable artifacts, not noise.*
