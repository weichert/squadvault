# OBSERVATIONS - Audience-Split Decision Closure: Option B

**Date:** 2026-05-29
**Status:** Decision-closure memo. Records the outcome of the deferred
question raised by `OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md`
sections 1-3. Sibling to the day's vision memo and the day's frontend-
inclusive gap analysis.
**Append-only:** Does not edit the predecessor memo. Records the decision
and points to the implementation.

---

## 1. Decision

**Option B** - Honor the audience split. The public archive surface
renders only the shareable segment of WEEKLY_RECAP content
(`--- SHAREABLE RECAP ---` ... `--- END SHAREABLE RECAP ---`). The
commissioner approve surface continues to render the full content
unchanged.

When the engine has emitted no `--- SHAREABLE RECAP ---` delimiter
(silence-over-fabrication case, e.g. W18-2025 platform-duplicate week),
the public surface renders a principled silence acknowledgment:
"The record is silent for this week." The artifact remains listed in
the public archive index; the week happened, the governance ran, and
silence is a governed outcome the record acknowledges.

---

## 2. Rationale

- **Vision-memo alignment.** The 2026-05-29 vision memo names the
  Writer's Room as the product and the substrate as precondition. The
  audit trail is substrate; it does not belong on the product surface.

- **Degenerate-case behavior.** Under Option A the public sees both
  audit trail and the "Creative narrative skipped" notice, which reads
  as broken. Under Option B the public sees only the silence
  acknowledgment, which reads as principled.

- **Trust bar already carries the trust work.** The CERTIFIED trust bar
  plus the docket ID is what tells members the artifact passed
  governance. Trace IDs in the prose duplicate that signal in a less-
  readable register; they do not add to it.

- **Design Brief alignment.** Part IX forbids analytics-adjacent
  affordances on the product surface; dense trace headers fit that
  pattern. Part VI's trust-bar-as-part-of-the-artifact rule is
  unchanged by the split.

- **Asymmetric implementation cost.** Option B's implementation is a
  single utility function plus a single conditional render block in
  the public single-recap page. Options C (toggle) and D (collapsed
  audit footer) add UI burden for an audience that has not asked for
  it.

---

## 3. Implementation pointer

Frontend repo `weichert/squadvault-frontend`:

- New utility: `src/lib/recap-audience.ts` exports
  `extractShareableSegment(contentMarkdown, artifactType): string | null`.
  Returns the shareable segment for WEEKLY_RECAP when delimiters are
  present; `null` when only audit content is present (silence case);
  passes through unchanged for non-WEEKLY_RECAP types.

- Modified page: `src/app/league/[id]/archive/recaps/[artifactId]/page.tsx`
  applies the utility and branches the body render. The bracketing
  trust bars are unchanged.

- Unchanged: commissioner approve surface
  (`src/app/league/[id]/approve/[artifactId]/page.tsx`), archive
  listing (`src/app/league/[id]/archive/recaps/page.tsx`), schema,
  migrations, API routes, governance tests.

Malformed-input handling: if the start delimiter is present but the end
delimiter is missing (not expected to occur in practice), the utility
renders from start to EOF and emits a `console.warn`. Bias-to-show
because the engine clearly intended a shareable segment if it emitted
the start delimiter.

---

## 4. What this closure does not do

- Does not change the engine's emission format. The engine continues
  to emit the delimiters as today. The split happens at the frontend
  rendering layer.

- Does not address the related F1 (RIVALRY_CHRONICLE_V1) seam noted
  in the 2026-05-28 memo section 5 (`week_index = 204510` packed
  integer, docket text `SV-2025-W204510-CHRONICLE-V03`). That seam is
  unrendered today (F1 surface deferred) and remains open for the
  F1-surface milestone.

- Does not promote the audit trail / shareable segment construct to
  a schema-level field. The delimiter-in-string format remains the
  engine's emission contract; a future schema-level split is a
  separable decision.

---

## 5. Cross-references

- **Predecessor:** `_observations/OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md`
  surfaced the question and recommended Option B.
- **Sibling:** `_observations/OBSERVATIONS_2026_05_29_WRITERS_ROOM_VISION_AND_HISTORICAL_CALIBRATION.md`
  - the vision memo whose framing aligns with this decision.
- **Sibling:** `_observations/OBSERVATIONS_2026_05_29_FRONTEND_INCLUSIVE_GAP_ANALYSIS.md`
  - section 9.1 open-decisions list, now reducible by one.
- **Design Brief Part IX** (anti-patterns) - the design-side rationale
  for keeping audit machinery off the product surface.

---

*Filing: `_observations/OBSERVATIONS_2026_05_29_AUDIENCE_SPLIT_DECISION_OPTION_B.md`.*
*Observation-only; no Map registration; no engine code or schema change.*
*The frontend change is recorded in this memo by pointer; the governance*
*event for that change is the frontend commit.*
