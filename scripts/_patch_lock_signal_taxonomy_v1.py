#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

MAP_PATH = REPO_ROOT / "docs/canonical/Documentation_Map_and_Canonical_References.md"

CONTRACT_PATH = (
    REPO_ROOT
    / "docs/canonical/contracts/signals/Signal_Taxonomy_Contract_v1.0.md"
)

CATALOG_PATH = (
    REPO_ROOT
    / "docs/canonical/specs/signals/Signal_Catalog_v1.0.md"
)

# ----------------------------
# Canonical content (v1.0)
# ----------------------------

CONTRACT_V1 = """# SquadVault — Signal Taxonomy Contract

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

"""

CATALOG_V1 = """# SquadVault — Signal Catalog

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

"""

# ----------------------------
# Utilities
# ----------------------------

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def write_file_exact(path: Path, content: str) -> bool:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"OK: created {path.relative_to(REPO_ROOT)}")
        return True

    existing = path.read_text(encoding="utf-8")
    if existing == content:
        print(f"OK: {path.relative_to(REPO_ROOT)} already matches canonical v1.0; no changes.")
        return False

    die(
        f"{path.relative_to(REPO_ROOT)} exists but does not match canonical v1.0 content.\n"
        f"Refusing to overwrite. Resolve manually or bump version."
    )

def insert_under_header_once(md: str, header_pat: str, line: str) -> tuple[str, bool]:
    if line.strip() in md:
        return md, False

    m = re.search(header_pat, md, flags=re.M)
    if not m:
        die(f"Missing required Documentation Map header anchor:\n  pattern={header_pat}")

    insert_at = m.end()
    md2 = md[:insert_at] + line + md[insert_at:]
    return md2, True

def patch_doc_map(path: Path) -> bool:
    if not path.exists():
        die(f"Missing Documentation Map: {path.relative_to(REPO_ROOT)}")

    s0 = path.read_text(encoding="utf-8")

    tier2_pat = r"^(##\s+Tier\s*2\s+—\s+Contract\s+Cards\s+\(Active\s+Governance\)\s*)\n"
    tier4_pat = r"^(##\s+Tier\s*4\s+—\s+Specs,\s+Schemas,\s+and\s+Technical\s+References\s*)\n"

    changed = False

    s1, c1 = insert_under_header_once(
        s0,
        tier2_pat,
        "- Signal Taxonomy Contract (v1.0)\n",
    )
    changed |= c1

    s2, c2 = insert_under_header_once(
        s1,
        tier4_pat,
        "- Signal Catalog (v1.0)\n",
    )
    changed |= c2

    if changed:
        path.write_text(s2, encoding="utf-8")
        print(f"OK: patched Documentation Map ({path.relative_to(REPO_ROOT)})")
    else:
        print("OK: Documentation Map already references Signal Taxonomy + Catalog; no changes.")

    return changed

def main() -> int:
    changed = False
    changed |= write_file_exact(CONTRACT_PATH, CONTRACT_V1)
    changed |= write_file_exact(CATALOG_PATH, CATALOG_V1)
    changed |= patch_doc_map(MAP_PATH)

    print("OK: canonical lock applied." if changed else "OK: no changes needed (already canonical).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
