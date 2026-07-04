# Observation - Unit 1.7b: Presentation Implementation + Lint (R5 closed)

Dated 2026-07-04/05 (Claude Code, Opus 4.8). Implements the landed Narrative Presentation Spec
v1.0 (`docs/Narrative_Presentation_Spec_v1_0.md`, `ce38f23`) at the code layer, closing finding R5.
Brief: `_observations/session_brief_unit_1_7b_presentation_implementation.md` (amended `213e211`).
Three founder gates (G1 structure design; G2 test plan; G3 diff + merge). Prod read-only; DB hash
`effb00e5` recorded start AND end, unchanged.

## What shipped (four-step playbook, in order)

1. **Structure module** - `src/squadvault/core/recaps/render/artifact_structure_v1.py`: parses an
   approved artifact's `rendered_text` into the spec section 3 canonical structure (masthead, title,
   narrative lede, [matchups], [transactions], [standings], facts block) exactly once, at the
   derived layer. Pure (no DB). Reuses the shared extractors (`extract_shareable_parts` +
   `render_transactions_block_v1`) so the facts block is byte-identical to the lifecycle emission
   and the L2 reference by construction. A malformed artifact returns `UnparseableArtifact` -
   surfaced, never repaired.
2. **Spec-4.1 renderer** - `plain_text_recap_v1.py`: `render_structure_plain_text(structure)`, a
   pure function of the structure. Masthead `PFL BUDDIES — WEEK {N} — {SEASON}` (caps, em-dash); the
   pre-R5 setext "=" underline is GONE; single `----` divider between lede and facts; facts block
   last, byte-identical. Empty (dormant) sections omitted - no placeholders.
3. **Consumer refactor** - `scripts/distribute_recap.py` (hot path) and
   `consumers/editorial_review_week.py` (Office review) now parse into the structure and render from
   it; both share one structure -> one renderer, so what the reviewer approves is what ships
   (Fork A). Unparseable artifacts are surfaced human-readably (P8b), never a trace or silent skip.
4. **Lint gap-fix** - `presentation_lint_v1.py`: L1 reconciled to the new masthead; L4 gains the
   setext "=" underline as the R5 REGRESSION GUARD (the W7 v27 markdown-in-group-text class can
   never silently return). Still standalone (no verifier import), L2 the one HARD rule.

## Two append-only corrections (ratified at G1/G2)

1. **"Full-output byte-identity" is STRUCK from the acceptance criteria** as self-contradictory. The
   spec's whole purpose (section 1) is to CHANGE the broken group-text chrome; requiring the full
   rendered output to be byte-identical would forbid the fix. Byte-identity is SCOPED (Gate 1 Q1):
   the facts block (L2 HARD) + all approved content (lede/narrative/bullets) are byte-identical; the
   chrome (masthead case/order, death of the setext underline) conforms to spec, and that chrome
   change IS R5. The regeneration guard is redefined accordingly (see the sweep below).
2. **The masthead is STRUCTURE, not content creation** (Gate 1 Q2). It is emitted from the
   artifact's own metadata (league, season, week) - the artifact's identity carried into its header.
   Spec section 6 forbids re-deriving FACTUAL CLAIMS (numbers, names, scores) from the database, not
   carrying an artifact's own header identity. Stated in `artifact_structure_v1` and
   `render_masthead_line_v1` docstrings, the one place section 6 could be misread.

## Ripple finding + ruling (Fork A)

Conformance changes to the shared renderer + lint ripple to ONE non-distribution path:
`consumers/editorial_review_week.py` (the Office pre-approval review), which renders + lints the
same clean form. RULING (founder, Fork A): one shared spec-conformant renderer - distribution AND
review both receive the fixed form; the review must show the shipped form (Fork B rejected as a
review-integrity gap). CLEAR (unaffected): `weekly_recap_lifecycle.py` uses only the facts-block
builder (untouched); `recap_verifier_v1.py` has its own SHAREABLE extractor and does not read the
masthead/underline (D-F holds). **Rider 3 confirmed with evidence:** the approval action
(`weekly_recap_lifecycle.py`) is a pure state flip - `UPDATE recap_artifacts SET state='APPROVED',
approved_by, approved_at` on the stored artifact by version; it does NOT re-render, store a clean
form, or compare rendered bytes; the renderer is not called on the approval path. Only the rendered
PRESENTATION changes; approval mechanics are unaffected.

## 34-artifact scoped byte-identity sweep (read-only; prod hash effb00e5 unchanged)

Every parseable approved artifact: narrative lede and facts block BYTE-IDENTICAL through the
refactored path (chrome diff expected and shown below). 34/34 clean:

```
2024: wk1 v43, wk2 v24, wk3 v24, wk4 v24, wk5 v26, wk6 v222, wk7 v27, wk8 v34, wk9 v26, wk10 v23,
      wk11 v23, wk12 v22, wk13 v34, wk14 v25, wk15 v23, wk16 v23, wk17 v24   (17 - all lede+facts BYTE-ID)
2025: wk1 v32, wk2 v23, wk3 v19, wk4 v22, wk5 v21, wk6 v22, wk7 v26, wk8 v18, wk9 v20, wk10 v27,
      wk11 v22, wk12 v24, wk13 v23, wk14 v30, wk15 v18, wk16 v21, wk17 v18   (17 - all lede+facts BYTE-ID)
34/34 parseable: zero content/facts drift.
```

## The 6 unparseable approved artifacts (data-hygiene register, A4-adjacent)

Surfaced, EXCLUDED from the regeneration guard, registered, NEVER repaired. Their published record
is untouched (the vault does not rewrite its past to satisfy a new parser). The lint's structural-
parse check runs pre-approval, so no NEW artifact can join this class. All six lack a SHAREABLE
RECAP narrative delimiter:

```
2024 wk17 v1        (an early 1467-byte stub; superseded by wk17 v24 which IS parseable)
2025 wk18 v15
2025 wk204510 v3    (week_index 204510 is itself garbage - a bad-week-index data artifact)
2025 wk204510 v4
2025 wk204510 v6
2025 wk204510 v7
```

A future founder decision (A4-adjacent) can examine whether any warrants attention; silence rule
applies - no synthetic ledes, no reconstructed facts blocks.

## Old-vs-new rendering (2024 wk1, the R5 change in the flesh)

```
OLD (pre-1.7b, the R5 defect):        NEW (spec 4.1):
  PFL Buddies — Season 2024, Week 1     PFL BUDDIES — WEEK 1 — 2024
  =================================     <no underline>
  <narrative ...>                       <narrative, byte-identical ...>
  ---                                   ----
  What happened this week:              What happened this week:
  - <bullets ...>                       - <bullets, byte-identical ...>
```

The `=====` setext underline (markdown H1 chrome that rendered as literal characters in the league
group text - the W7 v27 defect) is gone; the masthead is caps and correctly ordered; the lede and
facts block are unchanged to the byte. R5 is closed at the implementation layer: the group-text
rendering demonstrably contains no markup artifacts.

## Checks

- Full trio: ruff clean; mypy clean; pytest 2455 passed / 3 skipped (2434 baseline + 21 new).
- prove_ci: green on the clean tree.
- 26 frozen G2 obligations green (P1-P8 + P8b, L1-L5 firing+non-firing, M1-M2, D1x2, E1-E2, F1),
  including the L4 setext R5 regression guard and F1 provenance-marker survival (post-A8 ATTESTED /
  MANUAL:<tag> markers pass through the renderer byte-identically).
- Architecture + schema-drift gates green (no cross-layer import; no schema change).
- Prod DB hash `effb00e5` unchanged start->end; read-only throughout; nothing published.

## Out of scope (unchanged from the brief)

Web rendering against W.2 tokens (frontend unit, later); print renderer (deferred with the almanac);
any verifier change; any approval-flow change; voice/prompt iteration; Unit A9; no frontend changes.
