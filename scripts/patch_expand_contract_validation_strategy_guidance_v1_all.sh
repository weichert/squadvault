#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: expand Contract Validation Strategy Guidance to playbook (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"

"$python" - <<'PY'
from pathlib import Path
import sys

PATH = Path("docs/canon_pointers/Contract_Validation_Strategy_Guidance_v1.0.md")

NEW = """# Contract Validation Strategy — Guidance (v1.0)

Status: CANONICAL POINTER  
Applies To: All Tier 2 Contract Cards (Active Governance)

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- Core Invariants Registry (v1.0)
- Ops Shim & CWD Independence Contract (v1.0)

---

## Purpose

This document defines how Contract Cards must specify validation so governance is enforceable, testable, and durable.

A Contract Card without a validation strategy is incomplete.

---

## Definitions

### Invariant
A rule that must always hold.

If a rule cannot be validated (automated, gate-enforced, or auditable human review), it is not an invariant.

### Validation Types

1. **Automated (Unit / Property)**
   - Fast tests for deterministic logic and boundary rules.

2. **Integration**
   - Multi-component correctness (e.g., IO contracts, schema compatibility).

3. **Golden Path Proof**
   - End-to-end script proving the “real workflow” works.
   - Lives in `scripts/prove_*.sh` (shim-first; CWD independent).

4. **Gate-Enforced**
   - A hard stop in execution (forbidden patterns fail loudly).
   - Examples: “no autonomous publish,” “modules can’t write memory.”

5. **Human Review (Audited)**
   - Used only when the judgment cannot be automated.
   - Must be paired with auditable artifacts (approval logs, change records, reason codes).

---

## Minimum Bar for Tier 2 Contract Cards

Every Tier 2 Contract Card must include a **Validation Strategy** section that names:

- At least **one Automated** validation (if any deterministic logic exists)
- At least **one Gate-Enforced** validation (for a meaningful hard stop)
- If the contract affects a publishable artifact: at least **one Golden Path Proof**
- Any Human Review item must specify:
  - what artifact is reviewed,
  - by whom,
  - and what constitutes failure

---

## Required Template (Copy Into Contract Cards)

Add this section verbatim (and fill it in):

### Validation Strategy

**Automated**
- (List specific invariants + where they are tested)

**Gate-Enforced**
- (List forbidden actions that must fail loudly; name the gate location)

**Operational / Proofs**
- (List prove scripts, inputs, and what “PASS” means)

**Human Review**
- (Only if needed: what is reviewed, by whom, pass/fail criteria)

---

## Mapping: Common Invariant → Recommended Validation

- **Determinism (identical inputs → identical outputs)**
  - Automated (property test) + Golden Path Proof on fixed fixtures

- **Immutability / Append-only**
  - Gate-Enforced (refuse mutation) + Integration test for write paths

- **No autonomous approval/publication**
  - Gate-Enforced + Golden Path Proof showing explicit approval required

- **Versioning (edits/regenerations create new versions)**
  - Automated + Golden Path Proof verifying version increments and audit records

- **Boundary constraints (modules don’t write memory; AI doesn’t select signals)**
  - Gate-Enforced + Automated boundary tests (import rules, interface constraints)

- **Restraint / withholding behavior**
  - Golden Path Proof includes at least one withheld scenario + audit reason check

---

## Proof Script Conventions

- Location: `scripts/prove_*.sh`
- Must be: shim-first, CWD-independent, `set -euo pipefail`
- Must print a single-line PASS/OK summary at end
- Must accept explicit inputs (`--db`, `--league-id`, etc.)
- Must be safe to run repeatedly (idempotent; no destructive defaults)

---

## Canonical Declaration

Validation strategy is part of the contract.

A contract change is incomplete unless its validation strategy remains true and the referenced proofs/tests still pass.
"""

if not PATH.exists():
    print(f"ERROR: missing file: {PATH}", file=sys.stderr)
    raise SystemExit(2)

cur = PATH.read_text(encoding="utf-8")

if cur.strip() == NEW.strip():
    print("OK: validation guidance already expanded")
    raise SystemExit(0)

markers = [
    "# Contract Validation Strategy — Guidance (v1.0)",
    "Each Contract Card must declare:",
    "- Automated invariants",
    "- Gate-enforced invariants",
    "- Human-judgment invariants",
    "If an invariant cannot be enforced, it is not an invariant.",
]
if not all(m in cur for m in markers):
    print("ERROR: refusing to overwrite unexpected file shape", file=sys.stderr)
    raise SystemExit(2)

PATH.write_text(NEW + "\n", encoding="utf-8", newline="\n")
print("OK: expanded Contract Validation Strategy Guidance")
PY

echo "==> DONE"
