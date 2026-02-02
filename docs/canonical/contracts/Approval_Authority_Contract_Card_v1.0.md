# Approval Authority — Contract Card (v1.0)

Contract Name: APPROVAL_AUTHORITY  
Version: v1.0  
Status: CANONICAL  
Applies To: All SquadVault publication and editorial actions

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- SquadVault Core Engine — Technical Specification (v1.0)
- SquadVault — What We Are Not (Platform Guardrails) (v1.0)
- SquadVault — Data Ethics & Trust Positioning Memo (v1.0)
- Ops Shim & CWD Independence Contract (v1.0)
- Tone Engine — Contract Card (v1.0)
- Editorial Attunement Layer — Core Engine Addendum (v1.0)

---

## 1) Purpose

Approval Authority defines who may **approve**, **withhold**, **edit**, **regenerate**, or **override** narrative artifacts.

**AI drafts; humans decide.**  
Nothing is published without explicit human action.

---

## 2) Authority Model

### 2.1 Roles (Conceptual)

- **Approver**: may approve or withhold an artifact for publication.
- **Editor**: may propose edits that produce a new artifact version.
- **Regenerator**: may request regeneration (new version) from the same canonical inputs.
- **Administrator**: may configure delegation rules and role assignment.

These roles may be held by the same person in small leagues, but the authority boundaries remain the same.

### 2.2 Scope

Approval Authority applies to all artifact types and modules that produce artifacts intended for human consumption.

---

## 3) Hard Invariants (Non-Negotiable)

1. **No autonomous approval**  
   The system must not auto-approve, auto-publish, or auto-schedule publication.

2. **Approval is explicit and audited**  
   Approval must be a discrete action with a durable audit record.

3. **Edits create versions**  
   Any edit to an artifact must produce a new immutable version; no silent overwrite.

4. **Regeneration requires justification**  
   Regeneration must record a reason code (e.g., late ingestion, corrected data, editorial rewrite) and create a new version.

5. **Withholding is a valid outcome**  
   An artifact may remain withheld indefinitely without being treated as a failure.

---

## 4) Inputs & Preconditions

### Allowed Inputs

- Candidate artifact (draft output) plus its canonical trace metadata
- Window reference (league_id, season, week_index or equivalent)
- Artifact type and intended destination (if applicable)
- Actor identity (human principal) and asserted role
- Delegation configuration (explicit, versioned)

### Preconditions

- Artifact must be traceable to canonical inputs (or explicitly marked as not publishable).
- The system must be able to record an audit entry durably before finalizing an approval state change.

---

## 5) Outputs & State Changes

Approval Authority produces one of the following state transitions (examples; naming may vary in code):

- `DRAFT → APPROVED`
- `DRAFT → WITHHELD`
- `APPROVED → SUPERSEDED` (when a newer approved version exists)
- `APPROVED → WITHDRAWN` (rare; requires explicit reason + audit)

All transitions MUST be recorded as append-only events with actor identity and timestamp.

---

## 6) Delegation

Delegation is permitted but must be:

- Explicit (no implicit inference of authority)
- Versioned (changes tracked, reversible)
- Narrow (least authority required)
- Audited (who delegated what to whom, when, and why)

Delegation must never create a path to autonomous approval.

---

## 7) Audit & Traceability

Every action must record:

- Actor identity (human principal)
- Role asserted + role verified (where applicable)
- Artifact identifier + version
- Window reference
- Action taken (approve/withhold/edit/regenerate/override)
- Reason code (required for regeneration and overrides)

Audit records are append-only and must remain reconstructable.

---

## 8) Failure Modes & Correct Response

If authorization is uncertain, incomplete, or unverified:

- default to **WITHHELD**
- log a clear reason
- never “guess” authority

If audit recording fails:

- refuse the action
- do not change artifact state

---

## 9) Validation Strategy

### Automated
- No code path changes an artifact to APPROVED without an explicit approval action
- Edits always create a new version id
- Regeneration always records a reason code

### Operational / Proofs
- End-to-end proof demonstrates: draft → approve → export
- Attempted approval without required authority fails loudly

### Human Review
- Spot-check audit logs for completeness and clarity

---

## 10) Canonical Declaration

Any behavior not explicitly permitted is forbidden.

Changes require:
- explicit version bump
- Documentation Map update
- and (where applicable) a migration note.

