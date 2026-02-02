[SV_CANONICAL_HEADER_V1]

# SquadVault — Signal Taxonomy Contract

Version: v1.0  
Status: CANONICAL  
Authority Tier: Tier 2 — Contract Cards (Active Governance)  
Applies To: All signal classification, selection, and narrative input boundaries  

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- SquadVault — Documentation Map & Canonical References (v1.0)

Enforced By:
- (Reserved) Signal selection gates
- (Reserved) Writing Room intake validation

---

## 1. Purpose

This contract defines the canonical taxonomy for **signals** in SquadVault.

It establishes a stable vocabulary for:
- what qualifies as a signal
- how signals are categorized
- how signals may (and may not) be used downstream

This contract is binding. Any deviation is a defect.

---

## 2. Definitions

**Signal:** A unit of truth derived from ingested league data, expressed as a bounded, typed statement suitable for selection and narrative assembly.

**Event:** A raw ingested or canonicalized record (often source-shaped). Events are inputs; signals are curated outputs.

**Selection:** The deterministic subset of signals chosen for a given weekly window, producing the facts block and side artifacts.

**Narrative:** Any human-readable recap output built from selected signals. Narrative may be stylized, but may not fabricate beyond signal boundaries.

---

## 3. Signal Categories

Signals MUST be classified into exactly one of the following categories:

### 3.1 Transaction Signals
Roster-moving actions, including but not limited to:
- Waiver claims / BBID awards
- Free agent adds/drops
- Trades

### 3.2 Lineup and Match Signals
Start/sit, matchup outcomes, and weekly results when present in source data.

### 3.3 Performance Signals
Player or team performance outcomes when present in source data.

### 3.4 Meta / Governance Signals
System-level signals that affect interpretation or output constraints, including:
- withhold reasons
- intentional silence
- “summary-only” constraints

---

## 4. Signal Boundaries (Truth Contract)

### 4.1 No fabrication
Narrative MUST NOT invent details not present in the selected signals.

### 4.2 No implicit causality
Narrative MUST NOT attribute motives, strategy, or intent unless explicitly present in source data.

### 4.3 No hidden enrichment
Signals MUST be derivable from ingested data available in the repo’s canonical pipeline. Untracked enrichment is forbidden.

---

## 5. Intentional Silence

Certain event types may be intentionally excluded from narrative selection.

When this occurs:
- exclusion MUST be explicit and reasoned (e.g., `INTENTIONAL_SILENCE`)
- selection artifacts MUST retain counts for included/excluded and excluded-by-reason

---

## 6. Definition of Done

This contract is satisfied when:

- A canonical Signal Catalog exists (Tier 4) that enumerates:
  - signal IDs (stable)
  - category
  - required fields
  - selection defaults (include/exclude)
  - narrative permission boundaries
- Selection artifacts and gates can report:
  - included count
  - excluded count
  - excluded-by-reason breakdown
- Any regression that violates signal boundaries fails gates (Reserved).

