# SquadVault — Weekly Recap Context Temporal Scoping Clarification Addendum

**Status:** CANONICAL ADDENDUM

**Applies To:** Weekly Window Locking & Immutability Addendum (v1.0)

**Authority:** Subordinate to the Canonical Operating Constitution

**Version:** v1.0

---

## 1. Purpose

This addendum clarifies the temporal scoping of derived context layers
composed into a weekly recap prompt. The Weekly Window Locking &
Immutability Addendum (v1.0) governs window boundary mechanics and the
immutability of processed or withheld weeks. It is silent on derived
context layers that read across all seasons — for example,
`LEAGUE_HISTORY`, which computes all-time records, cross-season streaks,
and season-over-season comparisons. This addendum closes that gap.

## 2. Hard Invariant

All derived context composed into a weekly recap for approved week
(season, week) must reflect ledger state as of that week's approved end
— inclusive of that week, exclusive of every subsequent week. This
applies to first-generation recaps and to all regenerations, equally
and without exception. The immutability guarantee attaches to the week
as a temporal window, not to the first approved artifact alone:
regenerating a W13 recap later must yield the same derived context
block as generating it contemporaneously, because both are answering
the same question against an unchanged answer. Derivations that cannot
honor this scoping must be withheld from the recap context rather than
rendered against a wider horizon; silence remains preferred over
anachronism.

## 3. Relationship to Existing Contracts

This addendum extends the strict-scoping principle already asserted by
the PLAYER_WEEK_CONTEXT contract (*"All values reflect state as-of
approved week end"*) to every derived context layer composed into the
weekly recap prompt. It resolves the asymmetry in which SEASON_CONTEXT
and PLAYER_WEEK_CONTEXT are window-scoped by contract while LEAGUE
HISTORY-type derivations were previously unconstrained.

This addendum does not modify the Canonicalization Semantics Addendum
(v1.0). Canonical projections over `memory_events` may still change as
the ledger grows. The constraint introduced here is on the
*derivations* consumed by the weekly recap prompt, not on the
`canonical_events` projection layer itself.

## 4. Canonical Declaration

This addendum is binding on all SquadVault recap context derivations.
It clarifies, but does not modify, the immutability guarantees
established by the Weekly Window Locking & Immutability Addendum.
Changes require explicit versioning and review.

---

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
