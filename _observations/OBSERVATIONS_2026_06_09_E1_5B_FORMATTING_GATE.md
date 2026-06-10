# Observations - Unit E1.5b: Narrative formatting gate (closes R5)

**Date:** 2026-06-09
**Code commit:** `84284fe` · **Ledger commit:** this commit
**Predecessor:** E1.5a Narrative Presentation Spec v1.0 (`b075b8a`, founder/Fable).
**Closes:** finding R5 (published narratives carry no presentation formatting; no
formatting review in the publication path).

---

## What shipped

- `presentation_lint_v1.py` - pure, standalone deterministic lint implementing spec
  rules L1-L5. **L2 (facts-block byte-identity) is the one HARD rule**; L1/L3/L4/L5 are
  SOFT (flag, never block on style). Channel-aware (plain_text markup hygiene). Does not
  import the verifier (D-F: the verifier's factual contract is untouched).
- `plain_text_recap_v1.py` - the clean distributed S1-S5 assembler, lifted from
  `distribute_recap._format_for_paste_assist` so the publication path and the Office
  review share ONE renderer (verified output-identical).
- Lifecycle - shared transactions-block formatter (`render_transactions_block_v1`,
  parameterized prefix) + `derive_canonical_facts_block_v1` (independent re-derivation
  from `recap_runs` = the L2 byte reference). Render path output unchanged.
- `distribute_recap.py` - publication-path gate: SOFT flags warn; L2 hard-fail refuses
  distribution (rc 7).
- `editorial_review_week.py` - presentation checklist in the Office review.
- Tests - L1-L5 behavior, L2 tamper hard-fail, formatter forms, quiet weeks.

## Finding that shaped the integration: two artifact forms

Mid-session discovery (surfaced to founder; founder chose the publication-path approach):
the engine carries **two** recap forms.

- **Internal `rendered_text`** (DB `recap_artifacts`, companion JSON): deterministic
  summary + `--- SHAREABLE RECAP ---` markers + narrative; bullets as `  - ` (two-space).
- **Clean distributed `.md`** (what the spec's S1-S5 describes): title "PFL Buddies -
  Season X, Week Y", narrative, `---`, bullets as `- ` (one-space).

No current engine code produced the clean form as a reusable function - it was assembled
inline in the distribution script (chat-era `group_text_paste_assist` paste pipeline).
So E1.5b's real "pre-render structure / refactor consumers" work was lifting that
assembler into `render/` and pointing both the gate and the Office checklist at it. The
lint judges the CLEAN form; linting `rendered_text` would have fired every rule spuriously.

## L2 reference must be independent

A subtlety worth recording: the clean form's facts block is built from the same `bullets`
the artifact carries, so comparing them is identity-by-construction (catches nothing).
L2's reference is therefore re-derived from the canonical event ledger (`recap_runs`) via
`derive_canonical_facts_block_v1` - independent of the stored/rendered text - so a tampered
facts block (or a fabricated transaction in the narrative-adjacent block) actually fails.

## Where the gate runs (founder decision)

Founder chose "build the clean-form renderer + gate at the publication/distribution path."
The spec's L2 is enforced at distribution (where the clean form is produced), not at the
low-level approval call; the Office review surfaces the full checklist (SOFT + L2 status)
so the commissioner sees it before distribution. Faithful to spec section 4 ("in the
publication path") and the SOFT/HARD severity model.

## Verification

- ruff zero; mypy 160 files clean; full suite 2375 passed, 2 skipped (3.11).
- 168 render/lifecycle/determinism tests green after the render-path refactor (output
  unchanged). 12 new presentation-lint tests green (incl. L2 tamper hard-fail).
- prove_ci on a clean tree under the 3.11 interpreter (this is code, not doc-only).

## Carried forward

- web_prose typography is DEFERRED to W.2 (D-M); the lint is structural and channel-neutral
  there. print_almanac channel registered, deferred (L.8 on-ramp).
- E1.5a section 5: the first live recap (NFL Week 1, 2026) publishing through this gate is
  the acceptance evidence; defects there route to a spec revision memo, not silent edits.
