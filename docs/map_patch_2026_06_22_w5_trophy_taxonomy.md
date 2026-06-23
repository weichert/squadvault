# Documentation Map v1.7 - W.5 Trophy Taxonomy v1.2 Registration Patch

**Date:** 2026-06-22
**Patch type:** Single-entry registration (ratified D-J input; binding W.5 specification input)
**Predecessor Map:** Documentation Map v1.7
**Addendum precedent:** `map_patch_2026_06_10_w6_consent_governance.md` (format + registration
mechanism); `map_patch_2026_06_09_document_of_record.md`.
**HEAD at authoring:** `cd7a743`

This addendum is filed per Map v1.7 registration-as-commissioning mechanism. The Map's tier
structure, Compression Rule, Canonical Declaration, and all registered entries are unchanged.
Only the ratified W.5 trophy taxonomy is registered, so the Unit W.5 specification consumes a
committed (not carry-in) binding input.

---

## Why this registration

The Unit W.5 (Trophy Room) four-memo chain (selection-prep / decision-readiness / specification
increment 1 / registration, `_observations/OBSERVATIONS_2026_06_21_PHASE_11_W5_TROPHY_ROOM_*`)
names the trophy taxonomy v1.2 as its catalog of record. The decision-readiness (D5) and
registration memos both flag that the taxonomy, while ratified, lived only as a carry-in artifact
and was therefore not yet binding ("decided is not binding until registered"). This patch lands it
in-repo and registers it, so the spec's references to "taxonomy v1.2" resolve to a committed input
and the build does not begin on an unregistered catalog. The on-disk filename carries the true
header version (`v1_2`); the stale "v1_0" carry-in filename is not used.

## Registration

### docs/SquadVault_W5_Trophy_Taxonomy_DJ_Input_v1_2_2026_06_21.md

The DoR Part 3 Unit W.5 trophy custody surface consumes this taxonomy as its catalog. It is the
ratified D-J input (header version v1.2; one entry per trophy - name / qualification / custody
rule; constitutional pass run on all 37 artifacts), authored in the DECIDE lane and consumed by
the W.5 specification (increment 1). It is filed in-repo so Claude Code and Fable sessions read
the binding W.5 catalog directly. It is the catalog input, NOT the specification; the four W.5
chain memos are the specification chain.

**Entry:**

> **W.5 Trophy Taxonomy - D-J Ratification Input v1.2**
> (`docs/SquadVault_W5_Trophy_Taxonomy_DJ_Input_v1_2_2026_06_21.md`) - the binding catalog of
> record for Unit W.5 (the Trophy Room). 37 artifacts across Annual, Positional, Draft/Auction,
> In-Season, Live Record, and Permanent categories, plus the Championship Package (The Belt =
> traveling, The Ring = mint-and-keep, The League Trophy = communal perpetual). One entry per
> trophy: name / qualification (completed fact) / custody rule. Header version v1.2 (the "v1_0"
> carry-in filename was stale; the header governs). Ratified D-J input; consumed by the W.5
> specification chain (`_observations/OBSERVATIONS_2026_06_21_PHASE_11_W5_TROPHY_ROOM_*`,
> 2026-06-21). It is the catalog, not the spec; per-artifact champion + year and the C7-attested
> "Phony Football League" expansion are governed text surfaces resolved in the spec. Where it
> conflicts with any Tier 0-2 canonical document, the canonical document governs.

---

*Filing: `docs/map_patch_2026_06_22_w5_trophy_taxonomy.md`.*
*Registration mechanism: Map v1.7 registration-as-commissioning; absorbed into the next Map version.*
*Cross-references (already committed, 2026-06-21 six-commit set at/under `ac4141b`): the W.5 naming
ruling, the Trophy Room vs Mantel delineation, the DoR v2.1.2 supersession note, the PFL/C7
closure, and the Herlth A/V-Room name attestation.*
