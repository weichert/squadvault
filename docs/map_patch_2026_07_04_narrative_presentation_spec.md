# Documentation Map v1.7 - Narrative Presentation Spec v1.0 Registration Patch

**Date:** 2026-07-04
**Patch type:** Single-entry registration (ratified P1-P6; binding Unit 1.7a specification)
**Predecessor Map:** Documentation Map v1.7
**Addendum precedent:** `map_patch_2026_06_22_w5_trophy_taxonomy.md` (format + registration
mechanism); `map_patch_2026_06_10_w6_consent_governance.md`.
**HEAD at authoring:** `4f83bfd`

This addendum is filed per Map v1.7 registration-as-commissioning mechanism. The Map's tier
structure, Compression Rule, Canonical Declaration, and all registered entries are unchanged.
Only the ratified Narrative Presentation Spec v1.0 (Unit 1.7a) is registered, so the Unit 1.7b
implementation consumes a committed (not carry-in) binding spec.

---

## Why this registration

The Completion Plan Unit 1.7a defines how an approved weekly recap artifact is presented per
distribution channel - the published-narrative half of the R5 gap that the E1.5b formatting gate
(facts-block byte-identity) never addressed. Per Reset Memo v1.0 section 6.3 a binding document is
not binding until registered in the Map; this patch lands the spec in-repo and registers it so the
Unit 1.7b implementation brief references a committed spec, not a carry-in artifact. It is the
specification, NOT the implementation: Unit 1.7b (separate brief, per D-F) builds the renderings
and the standalone SOFT-tier presentation lint.

## Registration

### docs/Narrative_Presentation_Spec_v1_0.md

The canonical presentation contract for approved weekly recap artifacts. Ratified P1-P6 (founder,
2026-07-03/04). Defines one canonical artifact structure at the derived/render layer and three
channel renderings (plain-text/group-text rigorous, web mapped to W.2 type roles by reference,
print as constraints only in v1); the deterministic facts block is byte-identical across channels;
empty sections are omitted, never placeholdered; renderers clothe structure and never alter content.

**Entry:**

> **Narrative Presentation Spec v1.0 (Unit 1.7a)**
> (`docs/Narrative_Presentation_Spec_v1_0.md`) - the binding presentation contract for approved
> weekly recap artifacts, closing R5 at the spec layer. One canonical artifact structure defined
> once at the derived/render layer (masthead / title / narrative lede / per-matchup sections /
> transactions / standings note / facts block, facts block always last), with three channel
> renderings: plain-text/group-text (zero markup, structure via whitespace and case - the defect
> class is the W7 v27 markdown-in-league-text failure), web (maps to the W.2 design language's
> named type roles by reference - ratified D-M), and print/almanac-ready (constraints only in v1).
> The invariance law: each rendering is a pure function of structure; the facts block is
> byte-identical across every channel; renderers may clothe content (typography, spacing, dividers)
> and may never add, remove, reorder, or rephrase it (Vision Register item 7, operationalized).
> Empty sections are omitted, never placeholdered (silence over filler). Ratified P1-P6 (founder,
> 2026-07-03/04). Implementation and the standalone SOFT-tier presentation lint are Unit 1.7b
> (separate brief, per D-F); structural rules live in this spec and the lint, never in the verifier.
> Where it conflicts with any Tier 0-2 canonical document, the canonical document governs.

---

*Filing: `docs/map_patch_2026_07_04_narrative_presentation_spec.md`.*
*Registration mechanism: Map v1.7 registration-as-commissioning; absorbed into the next Map version.*
