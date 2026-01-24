# SquadVault — Signal Catalog

Version: v1.0  
Status: CANONICAL  
Authority Tier: Tier 4 — Specs, Schemas, and Technical References  
Applies To: Signal enumeration and narrative eligibility rules  

Defers To:
- SquadVault — Signal Taxonomy Contract (v1.0)
- SquadVault — Canonical Operating Constitution (v1.0)

---

## 1. Purpose

This catalog enumerates the canonical set of signal types used by SquadVault.

Each signal type includes:
- a stable ID
- a category
- minimum required fields
- default selection behavior
- narrative permissions and constraints

---

## 2. Stable Signal IDs

Signal IDs MUST be stable across time and versions.

Format:
- `SIG_<DOMAIN>_<NAME>`

Examples:
- `SIG_TXN_WAIVER_BID_AWARDED`
- `SIG_TXN_FREE_AGENT_ADD`
- `SIG_TXN_TRADE_COMPLETED`

---

## 3. Catalog

### 3.1 Transaction Signals

#### SIG_TXN_WAIVER_BID_AWARDED
- Category: Transaction
- Required fields:
  - team (winner)
  - player or asset
  - acquisition type = waiver / BBID
- Default selection: INCLUDE
- Narrative permissions:
  - May state the winning team acquired the player on waivers
  - Must not invent bid amounts unless present in source data

#### SIG_TXN_FREE_AGENT_ADD
- Category: Transaction
- Required fields:
  - team
  - player or asset
  - acquisition type = free agent
- Default selection: INCLUDE
- Narrative permissions:
  - May state team added player as free agent
  - Must not invent contract terms, FAAB amounts, or rationale unless present

#### SIG_TXN_TRADE_COMPLETED
- Category: Transaction
- Required fields:
  - teams (both)
  - assets exchanged (as present)
- Default selection: INCLUDE
- Narrative permissions:
  - May summarize trade terms as present
  - Must not infer “win/lose” unless computed as an explicitly-defined metric (Reserved)

### 3.2 Governance / Meta Signals

#### SIG_META_INTENTIONAL_SILENCE
- Category: Meta / Governance
- Required fields:
  - event_type or signal_type excluded
  - reason = INTENTIONAL_SILENCE
- Default selection: EXCLUDE from narrative, INCLUDE in counts
- Narrative permissions:
  - Must not leak excluded details
  - May report aggregate counts (e.g., “some signals were intentionally omitted”)

#### SIG_META_WITHHOLD
- Category: Meta / Governance
- Required fields:
  - reason code
- Default selection: WITHHOLD output when trigger conditions are met (Reserved)
- Narrative permissions:
  - If withheld, narrative output must not be generated

---

## 4. Notes

- This catalog is intentionally minimal at v1.0.
- Expand only when required by the process, and bump version when changing semantics.

