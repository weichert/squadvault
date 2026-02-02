[SV_CANONICAL_HEADER_V1]

# Editorial Attunement Layer — Calibration Contract (v1.0)

Contract Name: EAL_CALIBRATION  
Version: v1.0  
Status: CANONICAL  
Applies To: Editorial Attunement Layer (EAL) — calibration of restraint behavior

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- SquadVault Core Engine — Technical Specification (v1.0)
- SquadVault — What We Are Not (Platform Guardrails) (v1.0)
- SquadVault — Data Ethics & Trust Positioning Memo (v1.0)
- Editorial Attunement Layer — Core Engine Addendum (v1.0)
- Approval Authority — Contract Card (v1.0)

---

## 1) Purpose

This contract governs how Editorial Attunement Layer (EAL) restraint thresholds are tuned **without expanding scope**.

Calibration exists to:
- reduce overconfident narrative behavior in low-certainty weeks,
- preserve trust under ambiguity,
- and remain strictly within metadata-only constraints.

Calibration must never turn into “smarter EAL.”  
If calibration requires new inputs, the correct response is: **do less**.

---

## 2) Scope & Non-Goals

### In Scope (Allowed)
- Updating explicit numeric thresholds and deterministic parameters.
- Adding or adjusting reason codes for restraint outcomes.
- Versioned, human-controlled changes with audit trails.
- Changes that preserve EAL’s veto-only nature.

### Out of Scope (Hard Stop)
Calibration must never introduce or rely on:
- Learning from outcomes (approvals, edits, usage, engagement).
- Content semantics (text meaning, embeddings, sentiment, topic inference).
- Cross-window personalization or “group mood” inference.
- Any expansion of EAL inputs beyond permitted metadata.

---

## 3) Allowed Inputs for Calibration Decisions

Calibration decisions (human process) may consider:
- Operational observations from deterministic pipeline behavior (e.g., frequency of withheld outcomes).
- Known ingestion completeness signals (e.g., missing data rates as tracked by ingestion diagnostics).
- Explicit human feedback about over-restraint vs under-restraint (as notes), without converting it into automated learning.

Calibration must not be derived from engagement analytics or user behavior tracking.

---

## 4) Allowed Calibration Knobs

Calibration is limited to explicit, enumerable parameters such as:

- `MIN_SIGNAL_COUNT_FOR_NORMAL_TONE` (int)
- `MIN_CONFIDENCE_FOR_FULL_NARRATIVE` (float 0..1)
- `LOW_ACTIVITY_RESTRAINT_MULTIPLIER` (float)
- `MAX_ASSERTIVENESS_LEVEL` (enum ceiling)
- `MISSING_DATA_HARDSTOP_THRESHOLD` (float 0..1)
- `WITHHOLD_IF_DIAGNOSTICS_UNKNOWN` (bool)

Notes:
- Knobs must be explainable in one sentence each.
- Each knob must have a default value and a safe range.
- Knobs must not encode semantic interpretation (no “anger score,” “toxicity score,” etc.).

---

## 5) Change Control & Authority

### Who May Change Calibration
Only an authorized human actor (per Approval Authority) may change calibration parameters.

### How Changes Are Made
All calibration changes must be:
- explicit,
- versioned,
- and reversible.

Each change MUST record a `CalibrationChangeRecord` containing:
- actor identity
- timestamp
- previous values
- new values
- reason code (e.g., OVER_RESTRAINT, UNDER_RESTRAINT, INGESTION_DIAGNOSTICS_CHANGE)
- affected artifact types (if relevant)
- effective window (if gated)

No silent edits.

---

## 6) Determinism Requirements

- Given the same selection metadata + diagnostics + calibration params, EAL outputs must be deterministic.
- Calibration updates must never introduce nondeterministic logic.
- Removing EAL must not break correctness; it may only reduce restraint.

---

## 7) Validation Strategy

### Automated
- Determinism check: identical inputs → identical restraint directives
- Parameter schema validation: all knobs are explicit, typed, bounded
- Forbidden-input boundary: EAL cannot access content semantics or engagement metrics

### Operational / Proofs
- Regression proof run over a fixed set of windows confirms:
  - no new failure modes introduced
  - expected restraint rate changes are explainable
  - withheld outcomes remain valid and audited

### Human Review
- Review calibration change records for clarity and scope discipline
- Confirm changes don’t function as “semantic inference by proxy”

---

## 8) Failure Modes & Correct Response

If calibration is uncertain, untested, or risks scope creep:
- default to safer restraint (trust over coverage),
- and require a versioned change with explicit rationale.

---

## 9) Canonical Declaration

Calibration prioritizes trust over coverage.

Any behavior not explicitly permitted by this contract is forbidden by default.

Changes require:
- explicit version bump
- Documentation Map update
- and (where applicable) a migration note.

