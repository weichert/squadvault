# Documentation Map v1.7 - Provisional Section Patch

**Date:** 2026-05-16
**Patch type:** Provisional-section corrections (three entries)
**Predecessor Map:** Documentation Map v1.7 at `83201d9`
**Addendum precedent:** Map v1.6 section 4.2 patch at `46736a0`;
Map v1.6 template-registration patch at `f28be4d` (absorbed into v1.7 at `83201d9`).
**HEAD at authoring:** `8e572f9` (Surface Admission Test v1)

This addendum is filed per Map v1.7 registration-as-commissioning mechanism. The Map's
tier structure, Compression Rule, Canonical Declaration, and all registered entries are
unchanged. Only the Provisional Artifacts section is corrected.

---

## Corrections

### 1. Surface Admission Test -- now authored

Map v1.7 provisional section states: "Surface Admission Test -- predecessor-state not yet
met (one content-class admission attempted required); not yet authored."

**Correction:** The Surface Admission Test v1 was authored at `8e572f9` (2026-05-16).
The predecessor-state was adjudicated in the document itself (section 1), with the D5
delegation from E2-light selection-prep / spec section 9.3 as the adjudication authority.
The adjudication verdict: met under the D5 flexible reading; the A-cluster within-surface
content-class admission decisions constitute the required grounding friction.

**Corrected entry:**

> **Surface Admission Test v1** -- authored at `8e572f9` (2026-05-16); provisional in
> `_observations/OBSERVATIONS_2026_05_16_SURFACE_ADMISSION_TEST_V1.md`. Predecessor-state
> adjudicated in section 1 of the document. Promotes to `docs/` at the first actual
> cross-surface admission event (section 8 promotion criteria). Map registration at Tier 4
> follows promotion; not registered here because the document is still provisional.


### 2. F1 (Rivalry Chronicle) specification -- not listed

Map v1.7 provisional section lists E1, A1, A2, A3, E2-light as provisional surface specs
but does not list F1. The F1 specification was authored at `66265e0` (2026-05-14), after
Map v1.7 was authored at `83201d9`.

**Corrected entry (addition):**

> **F1 (Rivalry Chronicle)** -- `_observations/` provisional. Specification at
> `66265e0` (2026-05-14). Chronicle-generation infrastructure (chronicle verifier at
> `96d937b`; substrate-readiness assessment at `8abdff8`; generation shim at `4a71d53`)
> landed upstream of the spec. Requires one full cycle observed + founder election before
> Map registration per Phase 11 surface promotion criteria.

**Note on E3:** E3 is correctly absent from the provisional spec list. The E3 selection-
prep chain (`07d0bb7`, `859f9fc`) found E3 already implemented by
`src/squadvault/consumers/editorial_review_week.py`; Phase B shipped as a convenience shim
at `6ae691a`. No per-surface constitutional memo was authored for E3. The E-cluster is
exhausted for Phase 11 purposes per the finding memo at `6ae691a`.


### 3. Doctrine-to-Product Translation Table -- predecessor-state cleared

Map v1.7 provisional section states: "Doctrine-to-Product Translation Table --
predecessor-state not yet met; not yet authored."

The "predecessor-state not yet met" framing was informal: the Roadmap section 5.2 records
the Translation Table as "eligible but lower priority than the Admission Test. Could be
authored at any future session." The soft sequencing was "defer until (a) Admission Test
predecessor state is met, and (b) the founder elects." With the SAT now authored
(correction 1 above), condition (a) is met.

**Corrected entry:**

> **Doctrine-to-Product Translation Table** -- not yet authored. Eligible at any session
> per Roadmap section 5.2; lower priority than the Admission Test (now authored). The
> founder's election of pedagogical-artifact authoring over surface-spec or operational
> work is the remaining gate. No predecessor-state blockage.

---

## Corrected Provisional Artifacts section (complete, post-patch)

**Phase 11 framework artifacts:**

- Per-surface constitutional memo template v1.0 -- PROMOTED; registered at Tier 4 in
  Map v1.7.
- Surface Admission Test v1 -- authored at `8e572f9` (2026-05-16); provisional in
  `_observations/OBSERVATIONS_2026_05_16_SURFACE_ADMISSION_TEST_V1.md`. Promotes to
  `docs/` at first cross-surface admission; Map Tier 4 registration follows promotion.
- Doctrine-to-Product Translation Table -- not yet authored. Eligible any time;
  lower priority per Roadmap section 5.2.

**Phase 11 surface specifications (provisional; each requires one full cycle observed
+ founder election before Map registration):**

- E1 (Weekly Recap Distribution Surface) -- `_observations/` provisional.
- A1 (Hall of Fame & Shame) -- `_observations/` provisional.
- A2 (Draft History Vault) -- `_observations/` provisional.
- A3 (Championship Timeline) -- `_observations/` provisional.
- E2-light (Weekly Recap Archive) -- `_observations/` provisional.
- F1 (Rivalry Chronicle) -- `_observations/` provisional. Spec at `66265e0`.

**E3 note:** E3 found already implemented; no per-surface constitutional memo authored.
E-cluster exhausted per finding memo at `6ae691a`.

**Phase 11 Surface Roadmap** (`ba8b58a`) -- `_observations/` provisional; governs Phase
11 surface sequencing; not yet promoted.

---

## What this patch does NOT do

- Does not register any provisional artifact. All listed items remain provisional
  pending their respective promotion gates.
- Does not change any Tier 0-5 registered entry.
- Does not amend the Map's Compression Rule, Canonical Declaration, or registered entries.
- Does not register E3 (no per-surface constitutional memo exists; shim only).
- Does not promote or pre-register the SAT (it remains provisional pending the first
  cross-surface admission).
- Does not constitute Map v1.8. The next full Map version absorbs this patch (and any
  other patch addenda) when the founder elects a sweep.

---

## Cross-references

- `83201d9` -- Documentation Map v1.7 (the patched document)
- `46736a0` -- Map v1.6 section 4.2 patch (Option A addendum precedent)
- `f28be4d` -- Map v1.6 template-registration patch (format precedent; absorbed into v1.7)
- `bb0f325` -- Reset Memo v1.0 (section 6.2 registration-as-commissioning)
- `8e572f9` -- Surface Admission Test v1 (correction 1)
- `66265e0` -- F1 (Rivalry Chronicle) specification (correction 2)
- `6ae691a` -- E3 Phase B: finding memo + convenience shim (E3 note)
- `ba8b58a` -- Phase 11 Surface Roadmap section 5.2 (Translation Table predecessor note)
