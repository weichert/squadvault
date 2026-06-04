# Phase 11 — F1 Rivalry Chronicle Frontend Surface (Shipped)

**Date:** 2026-06-03
**Status:** Observational record of a cross-repo dispatch. No tier. Not registered in the Documentation Map.
**Frontend commit:** `57bb1d8` — `feat(rivalries): F1 Rivalry Chronicle archive surface goes live`
**Engine commit:** this memo (docs-only; skips prove_ci per established pattern).

**Predecessors / anchors:**

- `5a865a1` — Phase 11 surface-selection memo (parent; F1 admissible, contingent on substrate-readiness).
- `OBSERVATIONS_2026_05_10_PHASE_11_DECISION_READINESS.md` — landed D1 (substrate-readiness vs the Rivalry Chronicle v1 Contract Card) at **medium gap, 3–5 sessions of foundation work**, routing F1 *behind* foundation work and out of first-surface contention.
- `Rivalry_Chronicle_v1_Contract_Card.md` (Tier 2) — output-structure authority.
- `OBSERVATIONS_2026_05_29_AUDIENCE_SPLIT_DECISION_OPTION_B.md` — audience posture for WEEKLY_RECAP (audit content is not public).
- `scripts/sync_to_supabase.py` — engine→Supabase artifact mapping.

---

## 1. What shipped

The F1 Rivalry Chronicle archive surface is now live. Three new frontend files and one one-line flip of the archive index:

- `src/lib/chronicle.ts` — two presentational helpers (`parseRivalryTitle`, `stripTraceBlock`).
- `src/app/league/[id]/archive/rivalries/page.tsx` — index (every APPROVED `RIVALRY_CHRONICLE`, season-desc then anchor-week-desc, flat list).
- `src/app/league/[id]/archive/rivalries/[artifactId]/page.tsx` — public read-only detail.
- `src/app/league/[id]/archive/page.tsx` — F1 card `href: null` ("IN PREP") → `href: "rivalries"`; `emptyDetail` updated.

Validated in-sandbox against a fresh clone: apply-script output type-checks clean (`tsc --noEmit`, exit 0) and is idempotent on re-run. Purely presentational public reads + a label flip; no schema/RLS/state-machine touch, so the governance suite was not required for this commit.

---

## 2. The substrate-readiness assessment was superseded

The 2026-05-10 decision-readiness memo's D1 finding — *medium gap, F1 behind foundation work* — is **stale as of this session**. Direct inspection of the engine at `aac9083` shows the substrate fully materialized: the complete `chronicle/` package (`generate_`/`persist_`/`format_`/`input_contract_`/`matchup_facts_`), `consumers/rivalry_chronicle_{generate,approve}_v1.py`, `core/recaps/verification/chronicle_verifier_v1.py`, `core/exports/approved_rivalry_chronicle_export_v1.py`, `ai/creative_layer_rivalry_v1.py`, and a thick test suite (≈18 chronicle test modules). The foundation work D1 anticipated has since landed. This memo records the supersession so a future reader does not re-derive the stale gap.

---

## 3. Decisions taken (D1–D3), with reasoning

**D1 — Route family + naming.** New `archive/rivalries/` family mirroring the `archive/recaps/` idiom; flip the archive-index F1 card live. Segment named `rivalries` (reads naturally in URL and back-link); page titles remain "Rivalry Chronicle."

**D2 — Index-row label = hybrid parse-with-fallback.** The two franchises and the scope are **not** structured Supabase columns; they live only inside `content_markdown` (the contract formatter emits `## {team_a} vs {team_b}` as the second line). The index parses the first `## …` heading containing " vs " for each row's current version (one batched `.in()` query over `artifact_versions`, not an N+1 fan-out), falling back to a generic "Rivalry Chronicle" label when no contract header is present (the legacy upstream-quote format has none). The parse target is an engine-emitted structural line, not free prose.

**D3 — Detail content = strip the `## Trace` block for public.** The contract output carries a `## Trace` block (raw franchise IDs, canonical event fingerprints, deterministic `facts_block_hash`) — the same audit category the WEEKLY_RECAP audience-split deliberately hides from the public. `extractShareableSegment` passes `RIVALRY_CHRONICLE` through unchanged, so without intervention the trace would render publicly. `stripTraceBlock` removes only the Trace section (heading through the line before the next `## `, i.e. `## Disclosures`), preserving the Disclosures section and the optional `## Chronicle` narrative. Consistent with the Option-B posture; a small presentational transform, not engine-aware logic in the frontend.

---

## 4. Load-bearing finding: the discriminator mapping

`scripts/sync_to_supabase.py` maps engine `RIVALRY_CHRONICLE_V1` → Supabase `artifact_type = "RIVALRY_CHRONICLE"` (the `_V1` suffix is stripped because the Supabase CHECK constraint rejects it), `artifact_class = "F1"`, with `season` and `week_index` (anchor week) both populated (the sync casts both to `int`), and docket `SV-{season}-W{week:02d}-CHRONICLE-V{version:02d}`.

**Consequence for the surface:** the detail-page type guard checks `artifact_type !== "RIVALRY_CHRONICLE"`. Guarding on `RIVALRY_CHRONICLE_V1` would have 404'd every chronicle. The archive-index *count* is unaffected because it filters on `artifact_class = "F1"`, which is why "5 ENTRIES" displayed correctly even while the surface was dark.

---

## 5. Standing follow-ups (not blockers)

- **Real-device visual pass.** Not yet done on the rivalries index or detail. Confirm the matchup labels read cleanly off live approved prose and the trust-bar bracketing sits right on a phone.
- **Detail body heading redundancy (cosmetic).** The faithful body render shows the artifact's own `# Rivalry Chronicle v1` H1 + `## {a} vs {b}` H2 beneath the chrome H1 (which is the parsed matchup). This mirrors how E1 detail renders its own `# Week N` H1, and faithful rendering is the trust-posture default. If it reads as redundant on the device pass, trimming the generic body H1 is a one-line follow-up, not a rebuild.
- **Legacy upstream-quote format.** Still present in the engine (`render_rivalry_chronicle_v1`). The surface degrades gracefully (generic label, Trace-strip no-op) if such an artifact is ever synced, but no legacy-format chronicle is expected in the synced set.

---

## 6. Cross-repo continuity

This is the 13th cross-repo continuity surface. Prior twelve enumerated in the 2026-06-02 session brief; this dispatch adds the F1 rivalry surface going live.
