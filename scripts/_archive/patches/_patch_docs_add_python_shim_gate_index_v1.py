from __future__ import annotations
from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
DOC   = Path("docs/80_indices/ops/CI_Python_Shim_Compliance_Gate_v1.0.md")

HEADER = "[SV_CANONICAL_HEADER_V1]\n"

DOC_BODY = f"""{HEADER}
Contract Name: CI Python Shim Compliance Gate
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier 0)
  - CI Guardrails Index (Tier 1)

Default: Any behavior not explicitly permitted by this contract is forbidden.

—

## Purpose

Ensure patch wrappers and proof/gate scripts invoke Python via the repo-local shim:
- `./scripts/py`

This prevents PATH / venv ambiguity and keeps wrappers CWD-safe.

## Enforced By

- Gate script: `scripts/check_python_shim_compliance_v2.sh`
- CI runner: `scripts/prove_ci.sh`

## Canonical Patch Pairs

- Add gate:
  - `scripts/_patch_add_python_shim_compliance_gate_v1.py`
  - `scripts/patch_add_python_shim_compliance_gate_v1.sh`

- Standardize wrappers on shim:
  - `scripts/_patch_fix_patch_wrappers_use_py_shim_v5.py`
  - `scripts/patch_fix_patch_wrappers_use_py_shim_v5.sh`

- Refine enforcement:
  - `scripts/_patch_refine_python_shim_compliance_gate_v7.py`
  - `scripts/patch_refine_python_shim_compliance_gate_v7.sh`
"""

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing index: {INDEX}")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(DOC_BODY, encoding="utf-8")

    txt = INDEX.read_text(encoding="utf-8")
    link = "- [CI Python Shim Compliance Gate (v1.0)](CI_Python_Shim_Compliance_Gate_v1.0.md)\n"
    if link in txt:
        return

    # insert near top-level lists if possible; else append a small section
    insert_at = None
    for needle in ("## CI Guardrails", "## Guardrails", "## Ops", "## Index"):
        i = txt.find(needle)
        if i != -1:
            j = txt.find("\n", i)
            insert_at = j + 1
            break

    if insert_at is None:
        if not txt.endswith("\n"):
            txt += "\n"
        txt += "\n## Python Shim\n" + link
    else:
        txt = txt[:insert_at] + "\n## Python Shim\n" + link + "\n" + txt[insert_at:]

    INDEX.write_text(txt, encoding="utf-8")

if __name__ == "__main__":
    main()
