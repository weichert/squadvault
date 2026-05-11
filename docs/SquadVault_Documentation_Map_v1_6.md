# SquadVault — Documentation Map & Canonical References (v1.6)

**Status:** CANONICAL INDEX (Registry, Not Doctrine)

**Doctrinal source:** Reset Memo v1.0 (commit `bb0f325`).

**Predecessors:** v1.5 (interim; silently omitted the Compression Rule and the Canonical Declaration). v1.4 (last Map containing both verbatim).

---

## Purpose

This document is the operational index of SquadVault's binding artifacts and their tier of authority.

It is a **registry, not doctrine** (per Reset Memo v1.0 §6.4). The Map records which documents bind, at what tier, and under what conditions; it does not itself constitute binding doctrine. Authority resides in the Canonical Operating Constitution and the subordinate documents it governs.

---

## Registration as Commissioning

Per Reset Memo v1.0 §6.2, a SquadVault document acquires binding status by being registered in this Map. Authoring a document does not commission it; registration does. A document referenced in code, in another document, or in conversation but not registered here is provisional and must not be treated as authoritative.

This Map (v1.6) establishes the registration-as-commissioning mechanism in this preamble and registers itself as the first artifact under that mechanism (see *Self-Registration* below). v1.7 and onward operate under the established mechanism without bootstrap-style reflexivity.

### Curative Ratification (One-Time)

Per Reset Memo v1.0 §6.5, the ten documents enumerated in §5 of that memo (the "Finding-3 set," registered below at the tiers §5.1/§5.2 specified) were granted binding status by the memo itself, effective at commit `bb0f325`. This was a **one-time** curative amnesty. Documents authored after `bb0f325` are subject to registration-as-commissioning without exception: provisional until registered.

---

## Compression Rule

> Only Tier 0–2 documents should be loaded by default during design, development, or AI-assisted reasoning. Tier 3–5 documents are reference-only and must not be treated as authority unless explicitly invoked.

*(Verbatim from v1.4. Reinstated per Reset Memo v1.0 §3.1.)*

---

## Canonical Declaration

> This Documentation Map is a canonical index only. In the event of conflict, the Canonical Operating Constitution and subordinate Contract Cards take precedence.

*(Verbatim from v1.4. Reinstated per Reset Memo v1.0 §3.2.)*

---

## Authority Hierarchy (Binding)

### Tier 0 — Platform Constitution

- SquadVault — Canonical Operating Constitution (v1.0)

### Tier 0V — Vision Source

A parallel-to-Tier-0 designation for binding-vision documents. The binding-vision sections enumerated below fall within the default-loading expectation of the Compression Rule; reference-only sections do not.

- **SquadVault Business Plan**
  - **Binding-vision** (per Reset Memo v1.0 §4.2): Founder's Letter; §3 ¶¶1–2; §5 ¶¶1–3; §6; §7.
  - **Reference-only** (per Reset Memo v1.0 §4.3): §4; §8–§22; §23; §24; all 26 appendices.

  The Business Plan binds only as vision source for the enumerated sections. It does not bind operational, technical, or governance decisions; conflicts between binding-vision sections and Tier 0 / Tier 1 / Tier 2 documents resolve per the Canonical Declaration above.

### Tier 1 — Platform Operations, Guardrails & Trust

- What We Are Not (Platform Guardrails)
- Data Ethics & Trust Positioning Memo
- Operational Plan v1.1
- Platform & Writer's Room Compact v1.0
- Tier 5 Live Observation Cadence Doctrine v1.0 *(provisional)*

### Tier 2 — Subordinate Contracts (Contract Cards & Addenda)

**Contract Cards (Active Governance):**

- Creative Layer — Contract Card (v1.0)
- Writing Room Intake — Contract Card (v1.0)
- Writing Room — Selection Set Schema (v1.0)
- Writing Room — SignalGrouping Consumption & Boundaries (v1)
- PLAYER_WEEK_CONTEXT — Contract Card (v1.0)
- FAAB Outcome Insight — Contract Card (v1.0)
- Rivalry Chronicle — Contract Card (v1.0)
- Platform Adapter — Contract Card (v1.0)

**Subordinate Addenda:**

- Canonicalization Policy Addendum v1.0
- Canonicalization Semantics Addendum v1.0
- EAL Persistence Clarification Addendum v1.0
- Editorial Attunement Layer — Core Engine Addendum v1
- Weekly Recap Context Temporal Scoping Addendum v1.0

### Tier 3 — Technical Authority & Reference Notes

- Core Engine Technical Specification (v1.0)
- Fantasy Football Module Technical Specification (v1.0)
- Internal Note — Why The Editorial Attunement Layer Exists *(reference)*

### Tier 4 — Operational Control & Build Discipline

- Engineering Handoff Checklist (v1.1)
- Development Playbook (MVP)
- Recap Review Heuristic (Founder Use Only)

### Tier 5 — Archival & Reference

- Implementation Readiness Package (IRP)
- Technical Diligence Companion
- Contributor / Engineer Onboarding Brief
- Operational Scenarios & Edge Cases
- Second Module Qualification Checklist
- Canonical Folder Map & Ownership Guide
- AI Development Rules of Engagement
- Stop Before Suggesting X — Guardrails

---

## Conceptual Components (Non-Contract)

- **Social Layer** — CONCEPTUAL ONLY. No contract. No implementation. Deferred intentionally.

---

## Self-Registration (Bootstrap)

Per the registration-as-commissioning mechanism established above, this Map is the first artifact registered under that mechanism:

- **SquadVault — Documentation Map (v1.6)** → registered at Tier 1 as the operational index of binding documents.

This is a one-time bootstrap (per Reset Memo v1.0 §6.4). v1.7 and successor Maps register as ordinary Tier 1 entries within the main list above; no further self-registration step is required.

---

*Filing: `docs/SquadVault_Documentation_Map_v1_6.md`.*
*Format precedent: `.md` for new addenda and Map versions, per format-decision precedent at commit `14c6003`.*
*Predecessor lineage: v1.6 → v1.5 → v1.4. v1.5's silent omission of the Compression Rule and the Canonical Declaration is the failure mode v1.6 corrects; their explicit reinstatement here, alongside the registration of the ten Finding-3 documents and the codification of registration-as-commissioning, is the substantive content of v1.6.*
