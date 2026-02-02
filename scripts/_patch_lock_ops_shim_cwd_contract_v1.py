#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]

DOC_PATH = REPO_ROOT / "docs/canonical/contracts/ops/Ops_Shim_and_CWD_Independence_Contract_v1.0.md"
MAP_PATH = REPO_ROOT / "docs/canonical/Documentation_Map_and_Canonical_References.md"

DOC_V1 = """# SquadVault — Ops Shim & CWD Independence Contract

Version: v1.0  
Status: CANONICAL  
Authority Tier: Tier 2 — Contract Cards (Active Governance)  
Applies To: All operator entrypoints, gates, and proof scripts  

Defers To:
- SquadVault — Canonical Operating Constitution (v1.0)
- Documentation Map & Canonical References

Enforced By:
- scripts/check_shims_compliance.sh
- scripts/prove_golden_path.sh
- scripts/run_writing_room_gate_v1.sh
- scripts/gate_cwd_independence_shims_v1.sh

---

## 1. Purpose

This contract standardizes **deterministic operator entrypoints** using repo shims and guarantees **CWD independence** for operator-facing scripts.

The intent is to prevent fragile invocations and eliminate “works only from repo root” failures.

This contract is binding. Any deviation is a defect.

---

## 2. Definitions

**Repo Root:** the directory containing the `scripts/` directory and canonical repo layout.  
**Shim:** a stable wrapper that enforces deterministic Python import paths and canonical entrypoints.

Canonical shims:
- `./scripts/py` — python wrapper (shim-first execution)
- `./scripts/recap.sh` — operator-facing recap CLI shim

**CWD-independent:** script behavior is correct even when invoked from a non-repo current working directory, provided the script is addressed by a valid path.

---

## 3. Canonical Guarantees

### 3.1 Shim-first execution

Operator entrypoints MUST prefer:
- `./scripts/py` for Python execution of repo code
- `./scripts/recap.sh` for operator-facing recap CLI calls

### 3.2 Absolute resolution from script location

Operator-facing shell scripts MUST resolve paths relative to their own location using `SCRIPT_DIR`, and derive `REPO_ROOT` from that, e.g.:

- `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
- `REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`

Any internal references to repo files MUST use `"$REPO_ROOT/..."` (or equivalent derived absolute paths).

### 3.3 Deterministic output and clean smoke tests

Default behavior MUST remain deterministic and clean (no debug noise).
Debug logs MUST be gated behind `SV_DEBUG=1` (or an explicitly documented debug flag).

---

## 4. Forbidden Patterns

The following are forbidden in operator entrypoints and gates:

1) `./scripts/py ...` (or any variant that relies on caller environment)
2) Direct `./scripts/recap.py ...` invocation in operator docs or scripts (use `./scripts/recap.sh`)
3) Relative repo paths that assume repo root CWD, e.g.:
   - `find scripts ...`
   - `python3 Tests/...` (unless resolved from `REPO_ROOT`)
4) Debug output emitted by default (must be gated)

---

## 5. Debug and Logging Contract

### 5.1 SV_DEBUG

- `SV_DEBUG` is the canonical environment toggle for operator-level debug chatter.
- If `SV_DEBUG` is unset or not `1`, operator scripts MUST remain quiet except for required user-facing output.

### 5.2 Debug JSON dumps

Any JSON dump file emission MUST be behind explicit debug intent, e.g. `--debug-json` or `SV_DEBUG=1`, and must not occur by default.

---

## 6. CWD Independence Gate

A minimal gate MUST exist that proves shims and key operator scripts function from a non-repo CWD.

This is a required regression guard.

---

## 7. Definition of Done

This contract is satisfied when:

- Canonical shims exist and are shim-first + CWD independent:
  - `scripts/py`
  - `scripts/recap.sh`
- `scripts/check_shims_compliance.sh` enforces shim compliance using repo-root absolute paths
- Golden path and Writing Room gates pass from repo CWD:
  - `./scripts/check_shims_compliance.sh`
  - `./scripts/prove_golden_path.sh`
  - `./scripts/run_writing_room_gate_v1.sh`
- CWD independence gate passes:
  - `./scripts/gate_cwd_independence_shims_v1.sh`

Any future regression is a contract violation and must fail gates.
"""

MAP_INSERT_LINE = "- Ops Shim & CWD Independence Contract (v1.0)\n"


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


def patch_doc_map(path: Path) -> bool:
    if not path.exists():
        die(f"Missing documentation map: {path.relative_to(REPO_ROOT)}")

    s0 = path.read_text(encoding="utf-8")
    if MAP_INSERT_LINE.strip() in s0:
        print("OK: Documentation Map already references contract; no changes.")
        return False

    tier2_pat = r"^(##\s+Tier\s*2\s+—\s+Contract\s+Cards\s+\(Active\s+Governance\)\s*)\n"
    m = re.search(tier2_pat, s0, flags=re.M)
    if not m:
        die(
            "Documentation Map missing Tier 2 anchor header:\n"
            "Expected: '## Tier 2 — Contract Cards (Active Governance)'\n"
            "Refusing to patch."
        )

    insert_at = m.end()
    s1 = s0[:insert_at] + MAP_INSERT_LINE + s0[insert_at:]

    path.write_text(s1, encoding="utf-8")
    print("OK: inserted contract into Documentation Map (Tier 2).")
    return True


def main() -> int:
    changed = False
    changed |= write_file_exact(DOC_PATH, DOC_V1)
    changed |= patch_doc_map(MAP_PATH)

    print("OK: canonical lock applied." if changed else "OK: no changes needed (already canonical).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
