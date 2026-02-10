# Rivalry Chronicle Output Contract v1

## Purpose
Produce a rivalry-focused narrative artifact that is fun, readable, and *strictly derived* from canonical, verified facts within an approved scope/window. This contract governs **what the artifact is allowed to claim** and **how it proves lineage**.

## Contractual vs Non-Contractual

### Contractual (binding)
The following MUST hold for any Rivalry Chronicle output:
- **Scope declared:** Output MUST declare the exact scope (e.g., window_id(s), season range).
- **Fact authority boundary:** Any factual claim MUST be grounded in canonical deterministic facts/events. No new facts.
- **No inference of intent/emotion:** Output MUST NOT attribute motives, feelings, or intent unless explicitly present in canonical memory/events.
- **No analytics / advice:** MUST NOT include projections, rankings, start/sit, waiver advice, optimization, or “should have” coaching.
- **Auditability:** MUST include a trace/lineage block sufficient to reproduce the fact substrate and validate scope.
- **Silence is valid:** If rivalry basis is insufficient, output MAY be “WITHHELD” rather than padded with conjecture.

### Explicitly Non-Contractual (allowed to vary)
The following MAY vary without violating the contract:
- Exact prose, jokes, metaphors, and formatting
- Optional sections (headlines, “quote of the week”, etc.) **if** they do not introduce new facts
- Tone/voice modulation within Editorial Attunement constraints

## Required Output Fields (minimum)
At minimum, the artifact MUST include:

### 1) Header
- artifact_type: RIVALRY_CHRONICLE
- contract_version: v1
- scope: explicit window_id(s) or equivalent scope descriptor

### 2) Canonical Facts Block (mandatory)
- A deterministic, ordered list of rivalry-relevant canonical events in-scope
- Ordered strictly by approved window chronology
- Facts-only: results/scores only if canonical

### 3) Narrative Layer (optional)
- Derived connective prose only
- MUST NOT add facts; MUST NOT imply intent

### 4) Trace / Lineage Block (mandatory)
- window_id(s)
- canonical_event_fingerprints (or equivalent stable identifiers)
- deterministic_hash_of_facts_block (stable across identical inputs)

## Determinism Guarantees
- Identical canonical inputs + identical scope MUST yield identical Facts Block and identical deterministic hash.
- Narrative output may be stylistically variable only if an explicit, logged variant selection is used; otherwise narrative must be deterministic.

## Enforcement Mapping (Phase D, v1)
This contract is **enforced** by the contract surface completeness gate through:
- Presence of this file under docs/contracts/
- Inclusion in docs/contracts/README.md (contract surface index)
- Registry alignment checks (existing contract surface proofs/gates)

Runtime enforcement (artifact validation) is permitted only when backed by this contract.

---

# Rivalry Chronicle (v1)

## Enforced By

- scripts/gate_rivalry_chronicle_output_contract_v1.sh
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh

## Matchup Summary

## Key Moments

## Stats & Nuggets

## Closing

## Metadata rules

Metadata is a contiguous block of `Key: Value` lines immediately after header (optionally after one blank line).

Required keys:
- League ID
- Season
- Week
- State
- Artifact Type

Artifact Type must be `RIVALRY_CHRONICLE_V1`.

## Normalization rules

- Leading blank lines dropped.
- Header must be first line.
- Metadata upsert semantics: key uniqueness; last-write wins / overwrite.
- If required headings are missing, exporter may append a minimal scaffold (blank line separated).
