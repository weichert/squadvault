# SESSION BRIEF (SKELETON) - Unit E1.5b: Narrative formatting gate

**STATUS: SKELETON - NOT YET EXECUTABLE.** Blocked on one predecessor: the E1.5a
presentation spec (Fable). This prep artifact (engine HEAD `96ba951`) maps the verified
substrate and the four-step playbook; the `[FROM SPEC]` fields - the canonical structure
the lint enforces - come from E1.5a, not guessed here.

**Tool/model:** Claude Code / Opus 4.8. Closes finding **R5** (published narratives carry
no presentation formatting; no formatting review in the publication path).

## The two-session split (charter routing)

- **E1.5a - Presentation spec (Fable, DECIDE):** canonical artifact structure at the render
  layer (title block, per-matchup sections, transactions block, standings note) + per-channel
  renderings (web prose, plain-text group chat, print-ready); facts block byte-identical
  across renderings. Short spec in `docs/`. **Predecessor to this unit.** Calendar-gated:
  lands BEFORE NFL Week 1 so the first live recap publishes formatted (higher priority than
  E1.5b, which is the July->August window).
  - D-M (E1.5a concern): web prose consumes W.2's design language IF W.2 runs this summer,
    else channel-neutral. W.2 has NOT run -> E1.5a is channel-neutral for web typography for
    now. Does not block E1.5b's structural lint (structure, not typography).
- **E1.5b - Formatting gate (Opus, EXECUTE):** THIS brief. Depends on the E1.5a spec.

## Decided (do not re-litigate)

- **D-F: standalone lint, NOT a verifier category.** The verifier's contract stays purely
  factual; the formatting gate is a separate deterministic structural lint that runs
  alongside verifier pre-approval. (Founder-decided in the Document of Record.)

## Verified substrate (engine HEAD `96ba951`)

- **Render layer:** `src/squadvault/core/recaps/render/` - `render_recap_text_v1.py`,
  `render_deterministic_facts_block_v1.py`, `deterministic_bullets_v1.py`, etc. Step 1
  ("pre-render structure in `render/`") lands here.
- **Verifier pre-approval path:** `src/squadvault/core/recaps/verification/recap_verifier_v1.py`;
  lifecycle `src/squadvault/recaps/weekly_recap_lifecycle.py`. The lint runs ALONGSIDE this,
  not inside it (D-F).
- **Office review UI:** `src/squadvault/consumers/editorial_review_week.py` - where step 4's
  presentation checklist surfaces.
- **R5 evidence (the before-state):** `archive/recaps/2025/week_07__v27.md` (setext title,
  undifferentiated prose, raw bullet facts block; distributed over `group_text_paste_assist`
  where markup renders literally).

## Four-step playbook (per the Document of Record)

1. **Pre-render structure** in `render/` per the E1.5a spec's `[FROM SPEC: canonical
   structure - title block / per-matchup / transactions / standings]`.
2. **Refactor consumers** to produce the structured rendering per channel.
3. **Deterministic structural lint** running alongside verifier pre-approval:
   `[FROM SPEC]` rules - title present; facts block intact and unmodified; paragraph bounds;
   no orphaned markup for the target channel. **SOFT: flags, never blocks on style alone.**
   The ONE HARD condition: **facts-block-modified** (facts must stay byte-identical).
4. **Presentation checklist** in the Office review UI (`editorial_review_week.py`).

## Acceptance criteria (binary)

1. E1.5a spec exists and is registered in `docs/`; this brief's `[FROM SPEC]` rules trace to
   it.
2. Structural lint runs at recap pre-approval; flags formatting issues WITHOUT blocking on
   style; **hard-fails only on facts-block-modified** (facts block byte-identical preserved).
3. Lint is standalone (D-F) - the verifier's factual contract is unchanged (verify its tests
   still pass untouched).
4. Office review UI surfaces the presentation checklist.
5. Tests for the lint (planted formatting defect flagged; planted facts-block edit hard-fails;
   clean recap passes). ruff/mypy/pytest green; prove_ci clean (this IS code - not doc-only).
6. STATE.md discharges E1.5b; R5 marked closed; observation memo filed.

## OUT OF SCOPE

- Authoring the E1.5a spec (Fable's session).
- Adding formatting to the verifier's factual contract (D-F: standalone).
- W.2 design-language / web typography (deferred; channel-neutral until W.2).
- Blocking publication on style (SOFT by nature; only facts-block-modified is hard).

## OPEN until predecessor lands

All `[FROM SPEC]` fields (the canonical structure + per-channel lint rules) come from the
E1.5a presentation spec. Recommend: founder runs the E1.5a Fable session (it is the pre-Week-1
calendar priority), then "execute E1.5b" finalizes this skeleton against the spec.
