# OBSERVATIONS_2026_05_02 — H7 Cat B resolution: Position 2 selected

**Predecessor:** `_observations/OBSERVATIONS_2026_05_02_H7_CAT_B_ESCALATION.md` — the escalation memo that surfaced the architectural question this memo resolves.

**Stated purpose:** select Position 2 (remove the diagnostic-only reads, replace with derived counts) as the architecturally correct resolution to the H7 Cat B question. Cite the canonical documents that support the selection. Explain why Positions 1 and 3 were rejected. Frame the follow-on refactor session as the operational-completion deliverable.

This memo resolves the question. It does not execute the refactor. The four ingest sites continue to fail the gate at rc=1 until a separate session removes the reads; the gate's continued red state is now an explicitly-recorded *transitional* condition with a known resolution path, not an open architectural question.

## The question being resolved

From the escalation memo:

> "What the gate is for. Layer boundary, or source-fidelity contract? The gate's name suggests the former; its enforcement implements the latter. Resolve the divergence by amending one to match the other."
>
> "What category 3 (diagnostic-only reads) should be. Permitted with explicit allowlist category and inline rationale comments (Position 1), removed and replaced with derived counts (Position 2), or contingent on (1) being resolved first."

The escalation memo framed three coherent positions. Reading the canonical documents establishes which the architecture supports.

## Canonical reading

Three documents and the Constitution itself bear on the question.

**Canonical Operating Constitution (v1.0), System Boundaries:**

> "Core Engine owns memory, tone governance, and lifecycle"
> "Modules ingest domain events only"
> "Derived layers never write back into canonical memory"
> "Expressive layers never alter facts"

The Constitution's layering invariant addresses *write* permissions explicitly and exhaustively. It does not enumerate read permissions. This means the architectural read-permission model must be inferred from related guidance — and the EAL Persistence Addendum supplies that pattern.

**EAL Persistence Clarification Addendum (v1.0), the canonical pattern for cross-layer reads:**

> "EAL evaluation is window-scoped and non-durable... it does not accumulate state, profiles, or memory across windows... it reads no persisted state from any prior window... persistence is for audit and reproducibility... write-only from the evaluation perspective: the evaluation function never reads persisted directives."
>
> "Persisted directives must never influence evaluation of subsequent windows."

The pattern: **a layer may write to a sidecar surface, but the layer that wrote it cannot read it back to influence its own logic.** The forbidden mode is *read-influences-evaluation*, not *read-period*. Reads exist legitimately when they serve narrative derivation, canonicalization, or orchestration of those operations.

**Canonicalization Semantics Addendum (v1.0):**

Establishes that `memory_events` is the immutable ledger and `canonical_events` is the deterministic projection. The addendum is silent on read-permission topology — but it makes clear that the ledger is "the sole authoritative record of what happened" and that the canonicalization authority alone determines what is "best" within an action fingerprint group.

## What the canonical layering model says about the four sites

Reading the canonical docs together, the legitimate readers of `memory_events` fall into a coherent set:

1. **Core narrative derivation.** Render layer composing factual blocks from canonical events. The 5 `consumers/recap_*.py` allowlist entries plus `core/recaps/render/render_deterministic_facts_block_v1.py` fit here.

2. **Canonicalization authority.** The mechanism that produces `canonical_events` from `memory_events`. `core/canonicalize/run_canonicalize.py` fits here.

3. **Orchestration of canonicalization.** The operational layer that triggers ingest-then-canonicalize cycles. `ops/run_ingest_then_canonicalize.py` fits here.

These are the 8 allowlist entries at HEAD. Each is a layer the Constitution and addenda recognize as having a legitimate read relationship to the ledger.

The 4 ingest sites at HEAD fit none of these categories. Reading the surrounding code:

- `src/squadvault/ingest/_run_matchup_results.py:115` — print statement after a `=== Summary ===` banner, reporting count to operator stdout.
- `src/squadvault/ingest/_run_player_scores.py:99` — same pattern.
- `src/squadvault/mfl/_run_historical_ingest.py:262` — count print in a "Final Summary" block.
- `src/squadvault/mfl/_run_historical_ingest.py:272` — distinct-seasons listing in the same block.

None of these reads serves narrative derivation, canonicalization, or orchestration. Each is operator stdout reaching into the immutable ledger to display a count. **The diagnostic value is real but the architectural fit is not.**

## Position 2 selected

The canonical docs support Position 2: the four reads should be removed and replaced with derived counts.

The reasoning chain, in canonical-document order:

1. The Constitution's System Boundaries describe a layering model with `memory_events` as a Core asset.
2. The EAL Persistence Addendum establishes the canonical pattern: cross-layer reads are permitted only for layers with a recognized architectural relationship to the read surface (narrative derivation, audit reconstruction, orchestration).
3. Operator stdout diagnostic prints are not such a layer. They are non-architectural surfaces reaching into an architectural one.
4. The diagnostic information is fully preservable via derived counts. Each ingest script already has `total_events`, `total_inserted`, and `total_skipped` in scope. The post-ingest count of memory events of a given type is `pre_ingest_count + total_inserted` (where `pre_ingest_count` can be zero for first-time ingest, or queried before mutation if needed).
5. Removing the reads aligns with the Constitution's "Determinism overrides cleverness" invariant. A derived count from the ingest's own state is more deterministic than a query-after-mutation pattern, regardless of whether concurrent-writer races are practically possible in the current architecture.

## Why Position 1 was rejected

Position 1 (allowlist the four sites with a new "diagnostic-only" category) was rejected for three reasons:

1. **No precedent in the canonical docs.** None of the canonical addenda contemplate a "diagnostic-only" reader category. Adding it would establish a new architectural permission rather than exercising an existing one. The two prior allowlist expansions (`4bc8d09` 2026-01-31 adding canonicalize authority, `411ebf8` 2026-05-02 updating the canonicalize-authority path after a file move) added paths to *existing* categories. Adding diagnostic-only would be a different shape.

2. **Future-drift surface.** Once "diagnostic-only" is a permitted category, future code can label any read "diagnostic" to slip past the gate. The gate's strength is its exhaustive enumeration of legitimate readers; widening the enumeration with a fuzzy category undermines that strength.

3. **The diagnostic value is preservable without the read.** The case for Position 1 rests on preserving operator stdout output. That output can be preserved with derived counts. There is no operational benefit Position 1 provides that Position 2 sacrifices.

## Why Position 3 was rejected

Position 3 (rename the gate to match its enforcement) was rejected because the gate's name is correct as written when read against the canonical docs.

"No forbidden downstream reads from `memory_events`" describes the canonical layering model accurately:

- "Downstream" is correctly read as "outside the layers Constitution and addenda recognize as legitimate readers" — not as "consumer-layer-only."
- The gate's enforcement (any non-allowlisted read fails) implements this by exhaustive enumeration.
- The four ingest sites are downstream-from-the-architecture in the precise sense the gate's name describes: they sit outside the canonical reader layers entirely.

The escalation memo's framing of the gate's name as ambiguous reflects a less-careful reading of "downstream" than the canonical docs support. With the canonical reading, the gate's name and enforcement agree, and no rename is warranted.

## Implications for the gate

A single inline comment in `scripts/check_no_memory_reads.sh` cites this resolution. The comment is purely informational; no behavioral change to the gate. The four ingest sites continue to fail at rc=1 until the refactor session removes them.

The transitional state is preferable to silent ratification (Position 1) for the same reason the escalation memo preferred rc=1-with-recorded-question to rc=0-with-silent-allowlist: known-red gates with explicit architectural rationale are better than green gates with hidden architectural compromises.

## What this memo does not do

- **Does not execute the refactor.** The refactor is a separate session. Per the discipline established in today's prior commits, one topic per session: this session resolves the architectural question, the next session executes the code change.
- **Does not amend the canonical addenda.** The resolution is consistent with existing canonical text; no addendum needs updating. If a future session writes a new addendum codifying "diagnostic-only reads of `memory_events` are forbidden by default," that would be a strengthening of existing guidance, not a correction to it.
- **Does not project Track D timelines.** Per `OBSERVATIONS_2026_05_02_MVP_PER_IRP_COMPLETE.md`'s pattern, post-MVP forward projections belong in session briefs, not milestone or resolution memos.

## Follow-on session brief outline

The refactor session will be small in scope but careful in execution. Three sub-tasks:

1. **`_run_matchup_results.py:115` and `_run_player_scores.py:99`.** Both follow the same pattern: replace the post-ingest `SELECT COUNT(*)` with a derived `pre_count + total_inserted` calculation. The pre-count itself is either zero (first ingest) or read once at script start before any mutation, in which case the read is a *single* idempotency-gate read at script start (which is itself a diagnostic — it tells the operator "this script has already run for this scope"). Whether to keep that pre-count read is its own small decision, but it has clearer architectural standing as a "before-write fence" than the post-ingest reads do.

2. **`_run_historical_ingest.py:262` and `:272`.** The first is a total count; same treatment as #1. The second is a `SELECT DISTINCT season FROM memory_events` listing — slightly different shape because the script doesn't have the season list in scope from its own state. Two options: collect the season list as the script runs (preferable; tracks scope from inside-out), or accept that this specific diagnostic is the one that motivates Position 2's "the diagnostic information is preservable" claim being mildly weakened. Either is defensible; the refactor session decides.

3. **Gate verification.** After the refactor, `prove_ci.sh` should return rc=1 from a *different* check (banner paste gate's clean-tree precondition has fired before; rc=2 may be the new state until the working tree is clean) or rc=0 (depending on what the refactor session leaves in flight). Either way, the memory_events allowlist gate should pass cleanly with no entries needed for the four ingest sites.

The refactor session brief should be ~50 lines, cite this resolution memo, and follow the discipline carry-forwards from today (script-based applies, `printf` for commit messages, no chat-paste heredocs).

## Cross-references

- `_observations/OBSERVATIONS_2026_05_02_H7_CAT_B_ESCALATION.md` — the escalation memo this resolution closes.
- `SquadVault_Canonical_Operating_Constitution_v1.0.pdf` — System Boundaries section, the layering invariant.
- `EAL_Persistence_Clarification_Addendum_v1_0.docx` — the canonical pattern for cross-layer read permissions.
- `Canonicalization_Semantics_Addendum_v1_0.docx` — the immutable ledger and canonical projection model.
- `scripts/check_no_memory_reads.sh` at HEAD `49fed00` — the gate. Receives an inline comment citation in the commit immediately following this one.
- Commit `41e5127` (2026-01-30) — gate establishment with explicit allowlist.
- Commit `4bc8d09` (2026-01-31) — first allowlist expansion (canonicalize authority).
- Commit `411ebf8` (2026-05-02) — most recent allowlist expansion (canonicalize-authority path move).
- Commits `1c0c81b` (2026-03-23), `6d19a10` (2026-03-26), `b8ad0d7` (2026-03-28) — the three commits that introduced the four diagnostic reads, all 52–57 days after the strict gate landed.

## Append-only

This memo records the resolution. It does not edit the escalation memo or any other prior artifact; the only edit to a prior artifact is a single-line comment addition to the gate script in the commit immediately following this one.
