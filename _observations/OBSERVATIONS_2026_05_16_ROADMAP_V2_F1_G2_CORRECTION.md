# Roadmap v2 Standing Item Correction -- F1 G2 Entry
## SquadVault | Phase 11 | 2026-05-16

**Corrects:** OBSERVATIONS_2026_05_16_PHASE_11_ROADMAP_V2.md section 7.3
**Filed under:** Roadmap section 8.6 append-only discipline

---

## The error

Roadmap v2 section 7.3 contains this standing item:

  "F1 G2 automated distribution: pre-requisite for SAT cross-surface
  admission. Not yet implemented. Blocks F1 from advancing through the SAT."

Both claims are wrong.

---

## What the F1 spec actually says

F1 specification (OBSERVATIONS_2026_05_14_PHASE_11_F1_SPECIFICATION.md):

Section 3.3 (lines 129-131):
  "G2 -- Automated distribution (v1.1): scripts/distribute_rivalry_chronicle.py
  wrapping fetch_latest_approved_rivalry_chronicle_v1 + group-text send,
  analogous to E1's Track A automation. Deferred. The manual model is correct
  for v1 cadence."

Section 3.2 (line 58):
  "Election: Manual distribution at v1. No automated distribution script.
  distribution is a named v1.1 follow-on."

Section 9.3 (lines 364-365):
  "Unaffected. F1 under Reading 1 does not trigger content-class admission.
  The SAT predecessor-state remains unmet. Noted per prior spec chain
  carry-forward."

---

## Corrected characterization

G2 (automated distribution) is a v1.1 follow-on, deliberately deferred at
F1 spec authoring time. It is not an open gap and not a blocker. The manual
distribution model was the correct v1 election.

The SAT predecessor-state is unmet, but not because G2 is missing. F1 under
Reading 1 does not trigger content-class admission. The SAT is not blocked
by G2 -- it is simply not triggered by F1 v1 at all. The SAT predecessor-
state will be re-evaluated if and when a new content class is admitted.

---

## Corrected standing items entry (replaces Roadmap v2 section 7.3 F1 entry)

  F1 G2 automated distribution: deliberately deferred to v1.1 per F1 spec
  section 3.3. Manual distribution is the correct v1 election. No action
  required; not a blocker.

  SAT predecessor-state: unmet, but not because of G2. F1 under Reading 1
  does not trigger content-class admission (F1 spec section 9.3). The SAT
  is not currently triggered. Re-evaluate if a new content class is admitted.

---

## Origin of the error

The Roadmap v2 was authored (da9866b) from carry-forward memory without
cross-checking the F1 spec directly. The session brief's "F1 G2 automated
distribution -- pre-requisite for SAT cross-surface admission" framing was
inherited from prior carry-forward notes and was not verified against the
spec before landing in the Roadmap. The F1 spec was inspected this session
(8bc5ceb) and the error surfaced immediately on reading section 9.3.

Per Roadmap section 8.6 append-only discipline: this memo is the correction
record. The Roadmap v2 text is not silently patched.

---

Filed: 2026-05-16
HEAD at filing: 8bc5ceb
Corrects: da9866b (Roadmap v2) section 7.3 F1 G2 entry
