[SV_CANONICAL_HEADER_V1]

# Core Invariants Registry (v1.0)

Status: CANONICAL  
Applies To: SquadVault Core Engine and all modules, consumers, and operators

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- SquadVault Core Engine — Technical Specification (v1.0)
- SquadVault — What We Are Not (Platform Guardrails) (v1.0)
- SquadVault — Data Ethics & Trust Positioning Memo (v1.0)
- Ops Shim & CWD Independence Contract (v1.0)

---

## How to Use This Registry

- Each invariant has a stable ID (`INV-###`). IDs are never reused.
- Each invariant must remain true across refactors, modules, and artifact types.
- “Enforcement” lists the primary place(s) that should fail if the invariant is violated.
- “Validation” indicates the minimum proof required (automated preferred).

If a new feature cannot satisfy these invariants, the feature is out of scope.

---

## Invariants

### INV-001 — Memory is append-only (no mutation)
**Statement:** Canonical memory is immutable. MemoryEvents are append-only; prior events are never edited or deleted.  
**Scope:** Core Engine / Memory  
**Enforcement:** Memory event store write path; migration rules  
**Validation:** Automated (unit) + operational proof  
**Why:** Prevents temporal inconsistencies and silent history rewriting.

---

### INV-002 — Facts are never silently reinterpreted
**Statement:** Any correction is recorded as a new event; the system must not silently “reinterpret” or alter historical meaning.  
**Scope:** Core Engine / Narrative derivation  
**Enforcement:** Window immutability rules; deterministic facts boundary  
**Validation:** Automated (unit) + spot-check human review  
**Why:** Trust depends on preserving what was known when.

---

### INV-003 — Determinism upstream of drafting
**Statement:** Upstream pipeline stages (ingestion → memory → selection → tone directives) are deterministic: identical inputs yield identical outputs.  
**Scope:** Core Engine + Modules (pre-LLM)  
**Enforcement:** Contract boundaries; selection set derivation; tone directive generation  
**Validation:** Automated determinism tests + end-to-end proof on fixed fixtures  
**Why:** Debuggability and auditability require repeatable results.

---

### INV-004 — No autonomous publication
**Statement:** The system must never approve or publish artifacts autonomously. Approval is an explicit human action.  
**Scope:** Approval / Ops  
**Enforcement:** Approval endpoints/commands; publish/export gating  
**Validation:** Automated guard tests + end-to-end proof  
**Why:** Human authority is a core trust constraint.

---

### INV-005 — Edits and regenerations always create versions
**Statement:** Any edit or regeneration produces a new immutable artifact version; no silent overwrite.  
**Scope:** Artifacts / Versioning  
**Enforcement:** Artifact persistence layer; approval/export paths  
**Validation:** Automated (unit) + operational proof  
**Why:** Preserves audit trails and allows rollback/comparison.

---

### INV-006 — AI never decides “significance”
**Statement:** AI may draft and format, but must not decide what is significant, what “matters,” or what should be included/excluded.  
**Scope:** Writing Room boundary / Creative Layer  
**Enforcement:** Contract boundaries between selection and drafting; EAL veto-only constraints  
**Validation:** Automated boundary tests + human review of prompts/contracts  
**Why:** Prevents meaning-making drift and unaccountable editorial decisions.

---

### INV-007 — Restraint is a valid outcome (silence allowed)
**Statement:** Withholding or producing minimal output is valid when certainty is low; the system must prefer silence over fabrication.  
**Scope:** End-to-end behavior  
**Enforcement:** Withheld states; EAL restraint directives; deterministic facts rules  
**Validation:** End-to-end proof includes at least one “withheld” scenario  
**Why:** Epistemic humility is part of product integrity.

---

## Change Control

- Adding an invariant requires a version bump of this registry and an entry in the Documentation Map.
- Modifying an invariant requires explicit justification and a migration note if it affects tests or operator workflows.
- Removing an invariant is presumed forbidden unless the Constitution changes.


