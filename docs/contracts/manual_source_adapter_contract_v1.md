# Manual Source Adapter Contract - Addendum v1.0 (RATIFIED) - 2026-06-23

**Changelog v0.2 -> v1.0 (founder ratification, 2026-06-23):** addendum ratified; D3 retention resolved to content-addressed (workbook retained once + SHA-256 reference per row). Status DRAFT -> RATIFIED.
**Changelog v0.1 -> v0.2 (EXECUTE verification, 2026-06-23):** corrected the false "2018 fix is independent" claim - the 2018 de-contamination and the manual import meet at the Group D pick-type filter; the fix must be marker-aware (sections 2 and 8). Added the `LOAD_ROSTERS` build note (section 6.4). All other v0.1 claims verified against repo `75ad332`.

**Subordinate to:** Platform Adapter Contract Card v1.0; Event Payload Schema - Adapter Contract v1.0 (`docs/contracts/event_payload_schema_v1.md`, CANONICAL).
**Defers to:** Canonical Operating Constitution; Core Engine Technical Specification. Where this addendum conflicts with any of the above, they govern.
**Implements:** the founder ratification of the Manual Fact Import frame (`_observations/OBSERVATIONS_2026_06_06_..._DECISION_FRAME.md`), D1-D6, recorded in section 0.
**Status:** RATIFIED 2026-06-23 (founder). Build may proceed per section 8. **Anchor:** engine `main` `75ad332`.

## 0. Ratification record (append-only governance entry)

On 2026-06-23 the founder (commissioner + sole developer) ratified the Manual Fact Import frame:
- **D1 = (a)** - admit the manual-source adapter class as a new adapter under the existing Platform Adapter Contract, conditions C1-C4 binding. (Founder-explicit. Ratified knowing this admits a GENERAL capability, with 2021 as its first calibration instance, not a 2021-only patch.)
- **D2 = (a)** - provenance encoded in `external_source`.
- **D3 = content-addressed retention (founder-confirmed 2026-06-23)** - the origin workbook is retained ONCE in a content-addressed store and referenced by SHA-256 in each row's payload; this preserves complete re-inspectability without per-row duplication. (Resolves the v0.2 size-driven refinement; bytes-in-payload D3(a) and hash-only D3(c) both set aside.)
- **D4 = (a)** - reuse the founding-ceremony approval shape.
- **D5 = (a)** - add the verifier "human-attested" third path.
- **D6 = (a)** - this addendum is authored BEFORE any code; calibrate on 2021.

When landed (EXECUTE, doc-only), the frame's status updates OPEN -> RATIFIED append-only; this record supersedes nothing.

## 1. What the manual-source adapter is

An ingest adapter that conforms to the Event Payload Schema, whose `external_source` is a manual-class identifier and whose "platform" is a **retained human-attested artifact** (a spreadsheet, FFLM file, CSV). It produces the SAME canonical envelopes as any adapter; consumers read by `event_type` and never branch on source. The one property it cannot inherit from a live API is re-fetchability; it substitutes **re-inspectability**:

    re-derivability (re-fetch the API)  ->  re-inspectability (re-read the retained artifact)

A manual fact is as trustworthy as an adapter fact iff anyone can re-read the retained artifact and derive the same rows. That is the whole admissibility theory.

## 2. Event conformance (no new event type, no schema change)

Manual auction facts emit standard `DRAFT_PICK` envelopes per the Event Payload Schema: `payload.franchise_id`, `payload.player_id`, `payload.bid_amount`, `payload.mfl_type` (an explicit manual marker, e.g. `"MANUAL_AUCTION_WON"`, recording the artifact-native pick type), plus the retention fields in 3.C2. Group D #19-22 consume `DRAFT_PICK` unchanged; the provenance class (section 3.C1) rides `external_source` to the verifier so the awards surface as human-attested. **No engine, schema, or layer change** - this is an adapter only.

**Marker-aware filter invariant (load-bearing).** Provenance lives in `external_source`, never in `mfl_type`. Any award computation that selects winning auction picks MUST do so by EXCLUDING contaminant types (e.g. `mfl_type NOT IN ('AUCTION_BID', ...)`) and de-duping, NEVER by whitelisting a single live-source value such as `'AUCTION_WON'`. A whitelist would silently drop manual rows (their marker is not `AUCTION_WON`) and would also break for any future adapter's win-type string. This keeps the "consumers never branch on `external_source`" invariant intact while making the type filter source-agnostic. (See section 8 for the concrete interaction with the 2018 fix.)

## 3. The four binding conditions (deltas over the standard adapter contract)

A live-API adapter gets most of the contract for free. A manual adapter must carry explicitly the parts it cannot:

**C1 - Load-bearing provenance class.** `external_source = "MANUAL:<artifact-tag>"` (e.g. `"MANUAL:KP-AUCTION-2021"`). Never strippable; flows to every consumer and to the verifier verdict. This is what stops manual data masquerading as adapter-grade. (Conforms to the schema's required string `external_source`; the dedup tuple `(league_id, season, external_source, external_id)` therefore keeps manual and live facts in distinct identity spaces.)

**C2 - Retained source artifact, complete (no truncation).** The standard contract permits raw truncation because an API can be re-fetched; the manual class FORBIDS truncation - the origin artifact is retained whole and re-inspectable. **D3 RESOLVED (founder-confirmed 2026-06-23): content-addressed retention** - the origin workbook is retained ONCE in a content-addressed store, referenced by SHA-256 in each row's payload (`payload.source_artifact_sha256`, `payload.source_artifact_ref`). This preserves complete re-inspectability without the ~150x per-row duplication that bytes-in-payload (D3(a)) would incur on the ~338 KB workbook; hash-only (D3(c)) remains rejected as it defeats re-inspectability.

**C3 - Attributed approval as the ingest act.** The import CREATES fact, so it needs its own approval gate (reusing the founding-ceremony shape): who imported, when, against which artifact (by hash), logged. Recorded in the import-approval log; referenced from the envelopes.

**C4 - Partial truth, never gap-filling.** Only rows that extract cleanly AND reconcile to known identities import. Unmapped names (e.g. the validation's lone "J Warren") and any integrity-guard failure stay ABSENT - no interpolation, no "typical" value. Silence over speculation survives at the import layer.

**Determinism (re-pointed to artifact-native fields).** `external_id` is a deterministic function of artifact-native fields only - `(league_id, season, "DRAFT_PICK", franchise_id, player_id, bid_amount)` - and NEVER of SquadVault-internal state or a timestamp (the bulk artifact has none). Re-importing the same artifact yields byte-identical envelopes; `INSERT OR IGNORE` makes re-import a no-op.

## 4. Verifier third path (the provenance class reaches the verdict)

The verifier gains a third disposition for `DRAFT_AUCTION_DOLLAR` (and kin):
- adapter-derived coverage -> HARD re-derive (today);
- no coverage -> SOFT / surface (today);
- **manual-attested coverage -> re-derive against the IMPORTED rows** (fabrication relative to the import is still caught) **but disposition as "human-attested, unverifiable against a live source"** - never asserted as externally correct, never silently equated with adapter-grade ground truth.

A recap that misquotes the imported 2021 numbers is still caught; a correctly-quoted 2021 figure is surfaced as human-attested, not laundered to platform-grade.

## 5. Extraction and reconciliation discipline (codified from the KP validation)

Any manual ingest MUST:
- **Extract structure-aware:** bound to the data region (e.g. auction columns down to the `=SUM` row); exclude embedded analysis tables, notes, and formula cells. (A naive "all name+price pairs" scan corrupted a column during review; that failure mode is now a contract rule.)
- **Run integrity guards** appropriate to the artifact (e.g. the per-franchise budget guard: extracted spend <= the season budget). A guard failure means the extraction strayed; re-bound or report - never import the suspect region.
- **Reconcile identities and REPORT every gap:** franchise labels (which drift across seasons) to canonical IDs; source names to `player_id`. Unresolved identities are reported and their rows held absent (C4), never force-matched.

## 6. Calibration protocol - first exercise = 2021 (the frame's section-8 case)

After this addendum is ratified and the adapter is built:
1. Extract KP's 2021 tab structure-aware; budget-guard each franchise.
2. Reconcile identities; report and HOLD any unresolved row (C4).
3. Emit `DRAFT_PICK` envelopes under `external_source="MANUAL:KP-AUCTION-2021"`, `external_id` per section 3 determinism; retain the workbook (section 3.C2); log the C3 approval.
4. **Integrity anchor:** cross-check each imported pick's `(franchise, player)` against MFL's adapter-grade 2021 `LOAD_ROSTERS` seed - the half of each fact that IS platform-verified. Mismatches block that row. (Build note, verified: 2021 has 11 `LOAD_ROSTERS` rows - 10 real franchises plus one empty commissioner-init row, `transaction:"|"`, to skip; each real row's `players_added_ids` is a ~17-element player_id array.)
5. **Bias test:** check for a systematic price offset like 2020's +$1-2 before acceptance; if present, surface it, do not silently absorb it.
6. Only then do Group D #19-22 render 2021 - visibly human-attested via the section-4 disposition.

## 7. Boundaries (non-goals)

- No change to immutability, append-only, narratives-derived, or silence-over-speculation.
- No new layer and no governance carve-out: this is an adapter UNDER the existing Platform Adapter Contract.
- No engine or schema change; manual facts use the existing `DRAFT_PICK` envelope.
- This addendum authorizes no code by itself; ratification + the size-driven D3 confirmation gate the build.

## 8. Sequencing from here

1. Founder ratifies this addendum and confirms the D3 retention mechanism (section 3.C2). **[DONE 2026-06-23: ratified; D3 = content-addressed.]**
2. EXECUTE (doc-only): commit the addendum; update the frame OPEN -> RATIFIED append-only.
3. EXECUTE (code): build the manual-source adapter per this contract (the verifier third path included).
4. EXECUTE: run the section-6 calibration on 2021.
5. Group D #19-22 then render 2021 as human-attested.
- **The 2018 fix meets the manual import at the Group D pick-type filter - not fully independent (corrected per EXECUTE verification).** The 2018 `DRAFT_PICK` data is contaminated by `AUCTION_BID` intermediate-bid rows and one duplicate `AUCTION_WON`. The Group D award computation must de-contaminate by **excluding `AUCTION_BID` (and de-duping the duplicate win), expressed marker-aware** per section 2 - NOT by whitelisting `mfl_type='AUCTION_WON'`, which would silently exclude the manual 2021 rows and defeat the import. So written, the 2018 fix is a live-data-quality fix that can land before or independently of the manual adapter; only its EXPRESSION is coupled, and section 2 fixes the coupling.

## 9. Provenance / status

- Inputs: the ratified Manual Fact Import frame (D1-D6); the KP-sheet validation (98.6% across six independent seasons); the Event Payload Schema and Platform Adapter Contract Card.
- RATIFIED 2026-06-23 (founder). This addendum performs no code, import, or DB write itself. With ratification and D3 confirmed, the gates before the adapter build are cleared; the adapter build and the 2021 calibration are the next EXECUTE units, each with its own spec.
