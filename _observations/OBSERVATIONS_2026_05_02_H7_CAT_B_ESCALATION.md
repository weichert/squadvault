# OBSERVATIONS_2026_05_02 — H7 Cat B escalation

**Predecessor:** `_observations/OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md` (Category B from that memo); `_observations/OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` (re-grounding for this session); commit `411ebf8` ("CI: update memory_events allowlist for moved file (H7 Cat A)") — the morning commit that closed Category A and deferred this category.

**Stated purpose:** record the architectural question H7 Cat B surfaces, document why this session exits as escalation rather than allowlist expansion, and surface a procedural finding about the morning commit's framing of the four ingest sites.

This is Path C of the brief's three exit paths. No code changes this session.

## The architectural question

The gate `scripts/check_no_memory_reads.sh` is named "no forbidden downstream reads from memory_events." Its enforcement is `grep -RIn "FROM memory_events" src` minus an explicit allowlist of currently 8 paths. The gate's name and the gate's enforcement do not have the same scope.

The four ingest sites currently failing the gate are:

- `src/squadvault/ingest/_run_matchup_results.py:115`
- `src/squadvault/ingest/_run_player_scores.py:99`
- `src/squadvault/mfl/_run_historical_ingest.py:262`
- `src/squadvault/mfl/_run_historical_ingest.py:272`

Reading the surrounding code at HEAD `c2b158c`: every one of the four reads is in a `print` statement immediately after a `=== Summary ===` or `Final Summary` banner. None of the four results feeds a branch, a downstream selection, a persisted record, or a return value. They report counts and season lists to stdout for the operator running the ingest script. They are diagnostic-only.

The gate's enforcement model has three categories of reader, and the 8 existing allowlist entries cover only the first two:

1. **Functional consumers** that read `memory_events` to drive narrative, render, gating, or selection logic (5 entries: `consumers/recap_*.py`).
2. **Authority-layer reads** by canonicalize and ops orchestration (3 entries: `core/canonicalize/run_canonicalize.py`, `core/recaps/render/render_deterministic_facts_block_v1.py`, `ops/run_ingest_then_canonicalize.py`).
3. **Diagnostic-only reads** that print counts to stdout post-ingest with no influence on program logic. **No entry in the current allowlist.**

The architectural question this session escalates: should category 3 be permitted at all, and if so, on what basis?

There are three coherent positions:

### Position 1 — diagnostic reads are not "downstream reads" in the gate's intended sense

Under this reading, the gate is meant to enforce a layer boundary: "non-canonicalize, non-render, non-consumer code shouldn't be making memory_events part of its logic." A `print(count)` after ingest finishes, where the count is never used by anything else, is operator UX, not architecture. The fix under this position is allowlist expansion — but with two conditions that make it different from prior expansions:

- The gate's docstring or commit message must record the new permitted category explicitly. Past expansions (`4bc8d09`, `411ebf8`) added paths that fit existing categories (canonicalize-authority, canonicalize-authority-after-move). Adding a "diagnostic-only" category without recording it in the gate would conceal the rationale from future readers.
- The new allowlist entries should carry inline comments tagging them as diagnostic-only, so a future "is this read still diagnostic-only" review has a tripwire.

### Position 2 — diagnostic reads should be removed, not allowlisted

Under this reading, the gate is meant to enforce strict source-fidelity: only the named functional readers may touch memory_events, regardless of whether the read is "important." The fix is to remove the diagnostic prints, or to compute them from already-available counts (e.g., `total_memory = pre_ingest_count + total_inserted` rather than re-querying). Operator UX is preserved; the read is removed.

### Position 3 — the gate's name should be amended to match its enforcement

Under this reading, the question isn't about the four sites but about the gate. If the gate's enforcement is "any non-allowlisted read fails, regardless of purpose," it should be named accordingly ("no unallowlisted memory_events reads" or similar) and its docstring should be explicit that purpose-blindness is the design. The four sites are then either allowlisted with rationale (effectively Position 1) or removed (effectively Position 2), but the underlying ambiguity — what "downstream" means in the gate's name — gets resolved at the gate, not at the call sites.

This memo is not the venue to decide between these positions. The decision is Constitution-level: it touches what `memory_events` is permitted to be (a strictly-scoped functional store, or a queryable record-of-truth), what the gate is for (layer boundary, or source-fidelity contract), and what diagnostic surfaces ingest scripts are permitted to maintain.

## Why this session exits as escalation

The brief gave three exit paths and explicitly noted: "default exit if uncertain at decision time is Path C, not Path A. Allowlisting around an ambiguous read is the kind of small drift that calcifies; an honest 'I cannot decide today' memo preserves optionality and forces the decision into the right venue."

Three reasons Path A would have been wrong here:

1. **No precedent.** The two prior allowlist expansions (`4bc8d09` 2026-01-31, `411ebf8` 2026-05-02) added paths to layers that already had representatives in the allowlist. Adding diagnostic-only as a new category is a new architectural permission, not accounting cleanup.

2. **The brief's six-month code-review test fails.** The honest one-line rationale for each of the four sites is: "this print statement reports a memory_events count to the operator after ingest completes." A reviewer six months from now would reasonably ask: why is operator-stdout output worth a permanent allowlist entry, instead of being removed?

3. **The category is genuinely contested.** Position 2 (remove the reads) is a defensible reading; Position 1 (allowlist with new rationale) is also defensible; the choice between them depends on what the gate is *for*, which is not currently written down anywhere with sufficient precision to resolve the question.

Path B (refactor) was also rejected this session. The right refactor depends on Position 1 vs Position 2, which is itself the question being escalated. Refactoring without the position resolved would either over-correct (Position 1 wins, refactor wasn't needed) or under-correct (Position 2 wins, the refactor needs to be more aggressive than just removing this set of prints).

## Procedural finding — fourth instance of stale-assertion drift

This finding is recorded as a continuation of the drift pattern documented in `OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` (same date), where the priority list memo carried E1 and E2 as open when both were closed. This session surfaces a fourth instance, in a different memo, three hours apart from the amendment commit.

Commit `411ebf8` (this morning, 02:15 PT) asserts in its message body:

> "These are SELECT COUNT(*) idempotency checks, not consumer-layer downstream reads."

That description matches the SQL shape but not the code's purpose. Reading the four sites at HEAD: each read sits inside a `print(...)` immediately after a "Summary" banner, with the result interpolated into a stdout message and never consumed elsewhere. The "idempotency check" semantics are not present. There is no `if rows == 0` branch, no skip-if-already-ingested logic, no decision conditioned on the count.

The drift mode is the same as the E1/E2 entries on the priority list: an assertion about codebase state, written in a memo or commit message, propagated forward as if verified, but not re-derived against the code. In this case the morning commit body deferred a decision to "a future session" — this session — and shaped the framing of that future session via its assertion. The assertion was wrong, and the framing it implied (allowlist expansion is likely correct) was correspondingly wrong.

This is now the fourth instance:

1. The `prompt_text` column work — already complete in migration 0009 when a brief proposed it as new.
2. Player Trend Detectors T1 — firings already verified in production when a session attempted to start them as new.
3. The priority list E1/E2 entries (closed 2026-04-15 and 2026-04-01 respectively) carried as open on a memo dated 2026-04-28.
4. **(This instance)** The four ingest sites characterized as "idempotency checks" in commit `411ebf8` (2026-05-02 02:15 PT), discovered at HEAD `c2b158c` (2026-05-02 ~03:35 PT) to be diagnostic-only prints with no idempotency semantics.

That is now four instances within ~16 hours of repository history. The amendment memo's anti-drift commitment ("a fourth instance is no longer 'amend in place' — a fourth instance is the signal to redesign the priority-list mechanism") technically applies to priority-list-format drift specifically. This instance is not on the priority list; it is in a commit message body. But the failure mode is the same: assertions about code, written without re-deriving from the code, propagated downstream.

## Recommendation for resolution

The Constitution/Compact-level decision should clarify two things, in order:

1. **What the gate is for.** Layer boundary, or source-fidelity contract? The gate's name suggests the former; its enforcement implements the latter. Resolve the divergence by amending one to match the other.

2. **What category 3 (diagnostic-only reads) should be.** Permitted with explicit allowlist category and inline rationale comments (Position 1), removed and replaced with derived counts (Position 2), or contingent on (1) being resolved first.

A doc-read session is the right shape for this resolution, not a code session. Relevant documents: `EAL_Persistence_Clarification_Addendum_v1_0.docx`, `Canonicalization_Semantics_Addendum_v1_0.docx`, `SquadVault_Canonical_Operating_Constitution_v1_0.pdf`. The session brief for that resolution should reference this memo as the surfaced question.

`prove_ci.sh` will continue to fail at rc=1 on the 4 ingest sites until the resolution session ships. That is acceptable: a known-red gate with an explicitly-recorded architectural question is the brief's stated preferred state ("rc=0 or rc=1-with-an-explicitly-recorded-architectural-question"). It is strictly better than rc=0-with-a-silently-allowlisted-question.

## Cross-references

- `_observations/OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` — same-day amendment recording instances 1–3 of the drift pattern.
- `_observations/OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md` — the H1+H4 closure that exposed the silent gate failure.
- `_observations/PRIORITY_LIST_2026_04_28.md` — the priority list with H7 Cat B as an open item (status now corrected in the amendment memo).
- `scripts/check_no_memory_reads.sh` at HEAD `c2b158c` — the gate.
- Commit `41e5127` (2026-01-30) — gate establishment with explicit allowlist.
- Commit `4bc8d09` (2026-01-31) — first allowlist expansion (canonicalize authority).
- Commit `411ebf8` (2026-05-02) — most recent allowlist expansion, with the procedural-finding-relevant assertion in its message body.
- Commits `1c0c81b` (2026-03-23), `6d19a10` (2026-03-26), `b8ad0d7` (2026-03-28) — the three commits that introduced the four diagnostic reads, all 52–57 days after the strict gate landed.

## Append-only

This memo records the question and the session's exit. It does not edit any prior memo or commit message; the morning commit body is preserved as written, and the procedural finding is recorded here rather than amended back into `411ebf8`'s message.
