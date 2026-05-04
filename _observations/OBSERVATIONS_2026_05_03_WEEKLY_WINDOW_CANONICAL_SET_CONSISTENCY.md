# Weekly Window Immutability — canonical-set consistency audit

**Date:** 2026-05-03
**HEAD at memo-write:** `0fa1605` on `origin/main`
**Predecessor commits:**
- `bd680e3` — Phase 1 LEAGUE_HISTORY as-of-week scoping (`derive_league_history_v1` cutoff)
- `10e12a8` — Phase 2 conformance (verifier + franchise deep angles cutoff)
- `8082040` — W13 v22 dress-rehearsal validation memo
- `03b2d64` / `b1c27cc` / `c14c6c0` / `0fa1605` — dormancy-chain closure (orthogonal)

**Scope note:** Doc-read session. Five canonical documents plus the
`league_history_v1` module docstring plus the W13 validation memo.
**No code changes proposed in this session.**

**Predecessor session brief:** `session_brief_weekly_window_canonical_set_consistency_audit_2026_05_03.md`

---

## 1. Summary

Of **17 claims** surveyed across the 5-document canonical set and 2 supporting artifacts:

| Bucket | Count |
|---|---|
| CONSISTENT | 11 |
| STALE_CLAIM | 1 |
| OPEN_QUESTION | 4 |
| REDUNDANT | 1 |

**Headline:** the canonical-set is substantively consistent. The Hard
Invariant in the Temporal Scoping Addendum (T1) is mirrored by the
`league_history_v1.py` docstring (L1) and signature (L4), and is
empirically validated by the W13 memo (V1–V3). The single STALE_CLAIM
is the Implementation Note at the foot of the Temporal Scoping
Addendum, which described the pre-`bd680e3` shape and is now
historically stale. The four OPEN_QUESTIONs are governance-shape
questions (not bugs); none blocks the recap-quality thread from
proceeding to Step 2.

The brief anticipated that the Weekly Window Immutability Addendum
itself was the most likely source of STALE_CLAIM. It isn't. The Weekly
Window Immutability Addendum's text is sparse enough that it makes no
claims that the conformance work has invalidated; it speaks at the
window-boundary level, and the conformance work landed at the
derivation layer, which the Temporal Scoping Addendum properly owns.

---

## 2. Reads, in canonical order

### Read 1 — Canonicalization Policy Addendum v1.0 (`.docx`)
The constitutional substrate. Establishes three canonicalization
properties (deterministic-and-total, ephemeral, scoring-function-as-sole-authority)
and the reconstructability invariant ("running canonicalize twice with
the same memory_events ledger must produce identical canonical_events").
Authority: subordinate to the Constitution; binding on all
canonicalization implementations.

### Read 2 — Canonicalization Semantics Addendum v1.0 (`.docx`)
The vocabulary layer. Distinguishes `memory_events` (immutable ledger)
from `canonical_events` (deterministic projection). Critically asserts
that **canonical projections may change when the ledger grows** but
are always reconstructable. This is the addendum that makes "facts are
immutable" precise: the *ledger* is permanent, the *projection* is
ephemeral.

### Read 3 — Weekly Window Immutability Addendum (`.docx`)
The window-boundary layer. Three load-bearing claims:
- Weekly recap windows are lock-to-lock from authoritative lock
  timestamps.
- Lock timestamps are deduplicated and treated as immutable temporal
  boundaries.
- "Once a week has been processed or withheld, it is never
  reinterpreted or rewritten. SquadVault prioritizes historical
  accuracy over narrative completeness."

The addendum is brief — fewer than 200 words of substance — and
operates at window-boundary granularity. It does not address what
"never reinterpreted" means for derivations that read across all
seasons. That gap is what the Temporal Scoping Addendum closes.

### Read 4 — Weekly Recap Context Temporal Scoping Addendum v1.0 (`.md`)
The derivation-scoping layer. Most load-bearing document for this
audit. Verbatim Hard Invariant (markdown source, byte-exact):

> All derived context composed into a weekly recap for approved week
> (season, week) must reflect ledger state as of that week's approved
> end — inclusive of that week, exclusive of every subsequent week.
> This applies to first-generation recaps and to all regenerations,
> equally and without exception. The immutability guarantee attaches
> to the week as a temporal window, not to the first approved artifact
> alone: regenerating a W13 recap later must yield the same derived
> context block as generating it contemporaneously, because both are
> answering the same question against an unchanged answer. Derivations
> that cannot honor this scoping must be withheld from the recap
> context rather than rendered against a wider horizon; silence
> remains preferred over anachronism.

Two boundary clauses worth noting:

- **§3 boundary preservation:** "This addendum does not modify the
  Canonicalization Semantics Addendum (v1.0). Canonical projections
  over `memory_events` may still change as the ledger grows. The
  constraint introduced here is on the *derivations* consumed by the
  weekly recap prompt, not on the `canonical_events` projection layer
  itself." This is the cleanest seam between addenda in the entire
  canonical set.
- **Implementation note (non-binding):** "The current implementation
  of `derive_league_history_v1` is non-conformant: it accepts only
  `db_path` and `league_id` and reads all seasons without a window
  cutoff. Bringing the code into conformance with this addendum is a
  downstream code session." This is **stale** as of `bd680e3`.

### Read 5 — PLAYER_WEEK_CONTEXT Contract Card v1.0 (`.pdf`)
The adjacent-derivation layer. Hard Invariants include:
- "PLAYER_WEEK_CONTEXT is derived-only and non-authoritative"
- "All rows must be reconstructable from canonical and ingested
  sources"
- "No inference or gap-filling is permitted"
- "All values reflect state as-of approved week end"
- "Missing data must remain missing"

The Temporal Scoping Addendum (T6) explicitly extends PWC's "as-of
approved week end" principle to every derived context layer composed
into a weekly recap prompt. Symmetry is asserted at the addendum
layer; see Q4 for an architectural-shape question.

### Read 6 — `src/squadvault/core/recaps/context/league_history_v1.py`

Top-of-file docstring (lines 1–30, verbatim from the working tree at
`0fa1605`):

> Temporally scoped: every derivation composed into a weekly recap
> prompt reflects ledger state as of the approved window's end —
> inclusive of that week, exclusive of every subsequent week. See the
> Weekly Recap Context Temporal Scoping Addendum (v1.0) for the
> governing invariant.

Function signature (line 641):

```python
def derive_league_history_v1(
    *,
    db_path: str,
    league_id: str,
    as_of_season: int,
    as_of_week: int,
) -> LeagueHistoryContextV1:
```

The cutoff is **required keyword-only** — type-system-enforced; no
caller can omit it. Internal docstring further notes: "Making the
cutoff required surfaces any forgotten call site at import time."

`load_all_matchups` (line 214) accepts the cutoff as **optional**
(both-or-neither), with both-None preserving "backward compatibility
for consumers that legitimately operate over the full history." See Q3.

Phase 2 conformance also visible in the working tree:
- `franchise_deep_angles_v1.py:99-100, 113-114, 1548` — `as_of_season`/`as_of_week` threaded through.
- `recap_verifier_v1.py:116-169, 3057-3091` — `_load_all_matchups` accepts and applies the cutoff.

### Read 7 — `_observations/OBSERVATIONS_2026_04_20_W13_VALIDATION.md`
Empirical conformance evidence at `10e12a8`. Single approved W13 (2024)
candidate; cutoff regenerated against current ledger (which contains
78 canonical 2025 WEEKLY_MATCHUP_RESULT events). Result: 0 leak rows.
Block-level inspection confirms `seasons_available = 2010..2024` (no
2025), all `(Season YYYY, Week W)` parentheticals ≤ (2024, 13),
worst-season record "1-12 in 2024" = 13 games (consistent with
W13 cutoff).

Classification given: **CONFORMANCE_VALIDATED** (block-level, Phase 1).
**INFERRED** (not directly demonstrated) for Phase 2 — see V4 below.
The W13 candidate's prose did not invoke `_ALLTIME_PATTERN` or
`_SERIES_RECORD_PATTERN`, so verifier-side cutoff was not exercised in
a behaviorally discriminating way. Phase 2 conformance rests on Phase 1
results plus loader-level regression tests.

---

## 3. Consistency table

| # | Source | Claim (paraphrased) | Bucket | Evidence | Recommended action |
|---|---|---|---|---|---|
| C1 | Canonicalization Policy §2 | Canonicalization is deterministic and total | CONSISTENT | Aligns with Semantics §2.2; no contradictions | None |
| C2 | Canonicalization Policy §2.2 | Canonical projections are ephemeral (rebuilt, not accumulated) | CONSISTENT | Aligns with Semantics §2.2 | None |
| C3 | Canonicalization Policy §2.3 | Scoring function is sole authority for "best" selection | CONSISTENT | Aligns with Semantics §3 | None |
| S1 | Canonicalization Semantics §2.1 | `memory_events` is append-only and immutable | CONSISTENT | Constitution Core Invariant ("Memory is append-only and authoritative"); EAL Persistence Addendum aligns | None |
| S3 | Canonicalization Semantics §2.2 | Canonical projections may change as ledger grows | CONSISTENT | Explicitly preserved by Temporal Scoping §3 ("does not modify the Canonicalization Semantics Addendum") | None |
| W4 | Weekly Window Immutability | "Once a week has been processed or withheld, it is never reinterpreted or rewritten" | CONSISTENT | Reconciled with S3 by T1+T8: the *window* is immutable via cutoff-scoped derivation, not by freezing the ledger. Non-obvious but coherent. | None |
| T1 | Temporal Scoping §2 (Hard Invariant) | Derivations for week (S, W) reflect ledger state as-of week's end | CONSISTENT | L1 docstring mirrors verbatim; L4 signature enforces; V1–V3 validates | None |
| T2 | Temporal Scoping §2 | Applies to first-generation AND regenerations equally | CONSISTENT | L1 docstring covers; W13 regen at `10e12a8` exercises the regeneration path (V2) | None |
| T6 | Temporal Scoping §3 | Extends PWC's "as-of approved week end" to all derived context layers | CONSISTENT | P2 PWC contract states the principle; T6 generalizes; L1 implements for LEAGUE_HISTORY | None |
| T8 | Temporal Scoping §3 | Does NOT modify Canonicalization Semantics; scope is derivations only | CONSISTENT | Boundary clause; cleanly preserved | None |
| L4 | `league_history_v1.py:641` | Cutoff is required keyword-only on the public derivation entry point | CONSISTENT | Operationalizes T5 "silence over anachronism" at the type system; stronger than T5 strictly demands | None |
| T9 | Temporal Scoping addendum, Implementation note | "Current implementation of `derive_league_history_v1` is non-conformant: it accepts only `db_path` and `league_id` and reads all seasons without a window cutoff" | **STALE_CLAIM** | L4 signature shows the cutoff is now required (`bd680e3`); Phase 2 likewise (`10e12a8`); validated empirically (V1–V3) | Surgical edit candidate — see §5 |
| Q1 | Cross-doc | What counts as "validated" vs "inferred" conformance? | OPEN_QUESTION | V4: Phase 2 conformance is INFERRED, not behaviorally demonstrated; canonical set is silent on the validation standard | Surface for future governance; no urgency |
| Q2 | Temporal Scoping §2 | Withhold-vs-render behavior for derivations that *cannot* honor scoping | OPEN_QUESTION | T5 names the policy; current code makes withholding moot via type-system enforcement; future derivations with intrinsic at-window-incompleteness lack a documented workflow | Defer until a real case arises |
| Q3 | `load_all_matchups` signature | Cutoff is OPTIONAL on the helper; legitimate full-history readers exist | OPEN_QUESTION | L5 docstring declares the both-or-neither rule and explicitly preserves a "legitimate full-history" call shape; canonical set has no test for what counts as legitimate | Surface for future module-author guidance |
| Q4 | Cross-doc architectural shape | PLAYER_WEEK_CONTEXT is a Tier 2 contract card; LEAGUE_HISTORY is governed by an addendum + module docstring | OPEN_QUESTION | Symmetry asserted at addendum layer (T6) but uneven at the authority-hierarchy layer (Tier 2 vs Tier 3) | Defer; possible future contract-card promotion |
| C4↔S4 | Policy §3 / Semantics §4 | Reconstructability invariant restated in two addenda | REDUNDANT | Identical canonical claims, slightly different vocabulary | Note for housekeeping; no urgency |

---

## 4. Per-doc disposition

### Canonicalization Policy Addendum
3 claims surveyed (C1, C2, C3). All CONSISTENT. The addendum operates
at a distinct layer from the temporal-scoping work and is unaffected
by the conformance commits.

### Canonicalization Semantics Addendum
2 claims surveyed (S1, S3). Both CONSISTENT. The §2.2 claim that
"canonical projections may change when the ledger grows" is the
canonical-set's *most important* claim for understanding why the
Temporal Scoping Addendum had to exist: without S3, the Hard Invariant
would be self-contradictory.

### Weekly Window Immutability Addendum
1 claim surveyed (W4). CONSISTENT. The addendum is short and operates
at window-boundary granularity. The brief anticipated this would be
the most likely source of stale hedges. It isn't — the addendum makes
no claims at the derivation layer that the Temporal Scoping Addendum
or the conformance work could have invalidated. Its silence on
derivations is the gap the Temporal Scoping Addendum closes; that's
not staleness, that's intentional layering.

### Weekly Recap Context Temporal Scoping Addendum
4 claims surveyed (T1, T2, T6, T8) plus 1 implementation note (T9).
4 CONSISTENT, 1 STALE_CLAIM. T9 is the only material drift in the
canonical set. See §5 for the surgical edit recommendation.

### PLAYER_WEEK_CONTEXT Contract Card
2 claims surveyed (P2, plus Q4 architectural-shape question). P2
CONSISTENT with T1/T6. Q4 is the only architectural-shape question
worth raising and is OPEN_QUESTION rather than urgent.

### `league_history_v1.py` (working tree at `0fa1605`)
2 claims surveyed (L1, L4) plus 1 helper-shape claim (L5/Q3). L1 and
L4 CONSISTENT. L5 raises Q3 (legitimate full-history readers) — not a
defect, a documented seam.

### W13 validation memo
3 claims surveyed (V1–V3 confirming Phase 1; V4 inferring Phase 2).
V1–V3 directly support T1's CONSISTENT classification. V4 is the
basis of Q1.

---

## 5. Recommended follow-ups, in priority order

### 5.1 STALE_CLAIM — surgical edit (separate session)

The Implementation Note at the foot of `Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md`
described the pre-`bd680e3` shape and is now historically stale.
Suggested replacement (single block, single intent):

```markdown
## Implementation note (non-binding; historical)

At addendum-draft time, `derive_league_history_v1` was non-conformant:
it accepted only `db_path` and `league_id` and read all seasons
without a window cutoff. Conformance landed across two phases —
Phase 1 (`bd680e3`, Apr 2026) added `as_of_season` / `as_of_week` as
required keyword-only parameters on `derive_league_history_v1` and
its primary callers; Phase 2 (`10e12a8`, Apr 2026) extended the same
shape to `franchise_deep_angles_v1._load_all_matchups_flat` and
`recap_verifier_v1._load_all_matchups`. Block-level conformance was
validated against W13 (2024) at commit `10e12a8` with 0 leak rows;
see `_observations/OBSERVATIONS_2026_04_20_W13_VALIDATION.md`. This
note is preserved for historical context; the addendum itself does
not specify any implementation path.
```

The edit fits the brief's "one-line-class surgical" gate (single
markdown block, single intent, no logic change to the addendum). The
brief allows folding this into a separate commit in the same session
*after* the classification memo lands. Recommended commit message:

```
docs: temporal-scoping addendum implementation note retired to historical

Updates the addendum's non-binding implementation note to reflect
that conformance landed at bd680e3 / 10e12a8 and was empirically
validated at 8082040. The addendum's binding text is unchanged; only
the historical implementation note is updated.
```

This is a separate commit candidate, not part of this session's
classification memo commit.

### 5.2 OPEN_QUESTIONs — named follow-ups, no scheduled action

**Q1 — Validation standard.** The canonical set should at some point
articulate what counts as "validated" vs "inferred" conformance.
Right now: V3 declares Phase 1 CONFORMANCE_VALIDATED based on
block-level inspection of one regenerated W13 candidate; V4 declares
Phase 2 INFERRED because no candidate prose invoked the verifier's
cross-season patterns. Both stances seem reasonable, but the
canonical set is silent on the rule that distinguishes them. Possible
future addendum or governance memo. *Not urgent.*

**Q2 — Withhold-vs-render workflow.** T5 says derivations that
cannot honor scoping must be withheld. The current LEAGUE_HISTORY
implementation makes this moot via type-system enforcement (cutoff
required). A hypothetical future derivation with intrinsic
at-window-incompleteness — e.g., a derivation that depends on
end-of-season totals to compute a within-season metric — would need a
documented withhold workflow (logging? an alternative "WITHHELD"
context block? silence at the prompt layer?). *Defer until a real
case arises.*

**Q3 — Legitimate full-history readers.** `load_all_matchups`'s
optional cutoff is documented as preserving "backward compatibility
for consumers that legitimately operate over the full history." The
canonical set has no test for what counts as legitimate. Verifier and
deep-angles loaders pass cutoffs (verified in §2 Read 6). Future
module authors implementing new derivations might reach for the
helper without a cutoff and inadvertently render against a wider
horizon. Possible future module-author guidance: "Any consumer of
`load_all_matchups` that emits text into a weekly-recap prompt MUST
supply a cutoff." *Surface; not urgent.*

**Q4 — Architectural-shape symmetry.** PLAYER_WEEK_CONTEXT is a Tier
2 contract card. LEAGUE_HISTORY is governed by an addendum (Tier 3)
plus a module docstring. The Temporal Scoping Addendum (T6)
generalizes PWC's strict-scoping principle to all derivation layers,
which is the right *governance* answer, but the architectural shape
is uneven. Open question: should LEAGUE_HISTORY have its own contract
card, or is the addendum-anchored governance correct because
LEAGUE_HISTORY is a recap-context derivation rather than a
domain-data layer? *Defer; possible future contract-card promotion if
LEAGUE_HISTORY ever gains its own approved exports beyond the recap
prompt.*

### 5.3 REDUNDANT — note only

C4 (Policy §3) and S4 (Semantics §4) restate the reconstructability
invariant in slightly different vocabulary. Both are CANONICAL
ADDENDA; both bind. The duplication may serve self-containment of
each addendum. *No urgency. Possible consolidation in a future
doc-housekeeping pass.*

---

## 6. What this memo does NOT do

- **No code changes.** Conformance shipped at `bd680e3`/`10e12a8` and
  was validated at `8082040`. No further code work is in scope here.
- **No reopening of the architectural decision.** The Temporal Scoping
  Addendum's Hard Invariant is the contract; this audit checks
  consistency *against* it, not whether it's the right invariant.
- **No multi-doc rewrites.** The single STALE_CLAIM (T9) gets a
  recommended surgical edit; the actual edit happens (if at all) in a
  separate commit in this same session, or in a future session.
- **No addressing of Steps 2–3 of the four-step plan.** Score-string
  pre-rendering and streak-verb pre-computation are code sessions;
  out of scope for this doc-read.

---

## 7. Disposition vs. Steve's user memory

`userMemories` currently includes:

> "**DATA_LAYER bug**: `league_history_v1` LEAGUE HISTORY block not
> scoped to as-of-week-N, allowing future-week data to appear in a
> W13 recap (Weekly Window Immutability question — classification
> memo pending)"

This is stale relative to the artifact trail. The "DATA_LAYER bug"
framing was correct in April; it is no longer descriptive of the
current state. The memory should be updated to reflect:

- Phase 1 scoping landed at `bd680e3`.
- Phase 2 scoping landed at `10e12a8`.
- Block-level conformance validated at `8082040` against W13 (2024).
- The "classification memo pending" obligation is closed by *this*
  memo at HEAD `0fa1605`.
- The remaining W13-era issues worth tracking are MODEL_SIDE
  (score-rendering hyphen-vs-decimal ambiguity, streak verb
  relational inversion). Both are still standing; both are code-
  session material; both are out of scope here.

Steve's anti-drift discipline §5 governs: "Memory may be stale; the
artifact trail is authoritative. When they conflict, prefer the
artifact trail and update memory." Recommended memory edit applied
post-session.

---

## 8. Stop signal

Classification recorded. No code work proposed in this session. The
recap-quality thread can advance to Step 2 (score-string
pre-rendering) with confidence that the contract layer is sound and
the single material drift (T9 implementation note) is named with a
surgical-edit recommendation rather than left to fester.

The STALE_CLAIM at T9 is the only addendum-text edit recommended by
this audit. The four OPEN_QUESTIONs are named for awareness; none
gates further work.

Read first. Classified. Memo written.
