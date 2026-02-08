from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROVE_CI = REPO / "scripts" / "prove_ci.sh"
GATE = REPO / "scripts" / "gate_proof_surface_registry_excludes_gates_v1.sh"

DOC_GUARDRAILS_INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
DOC_PROOF_REGISTRY = REPO / "docs" / "80_indices" / "ops" / "CI_Proof_Surface_Registry_v1.0.md"

DOC_RULE_BEGIN = "<!-- SV_RULE_GATE_VS_PROOF_BOUNDARY_v1_BEGIN -->"
DOC_RULE_END = "<!-- SV_RULE_GATE_VS_PROOF_BOUNDARY_v1_END -->"

DOC_RULE_BLOCK = f"""\
{DOC_RULE_BEGIN}
## Gate vs Proof Boundary (Canonical)

**Rule:** CI **gates** (`scripts/gate_*.sh`) are **not proofs** and must **never** appear in this registry.

- This file lists **proof surfaces** only (typically `scripts/prove_*.sh`).
- Enforcement scripts belong in the **Ops Guardrails Index** instead.

This boundary is CI-enforced by: **gate_proof_surface_registry_excludes_gates_v1**.
{DOC_RULE_END}
"""

INDEX_ENTRY_BEGIN = "<!-- SV_GATE_PROOF_REGISTRY_EXCLUDES_GATES_v1_BEGIN -->"
INDEX_ENTRY_END = "<!-- SV_GATE_PROOF_REGISTRY_EXCLUDES_GATES_v1_END -->"

INDEX_ENTRY_BLOCK = f"""\
{INDEX_ENTRY_BEGIN}
- **gate_proof_surface_registry_excludes_gates_v1**  
  **Script:** `scripts/gate_proof_surface_registry_excludes_gates_v1.sh`  
  **Purpose:** Fails CI if `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md` contains any `scripts/gate_*.sh` entries.  
  **Why:** Gates are enforcement; proofs are demonstrations. Mixing them makes drift easy and weakens the registry’s meaning.
{INDEX_ENTRY_END}
"""

PROVE_CI_WIRE_BEGIN = "# SV_GATE: proof_registry_excludes_gates (v1) begin"
PROVE_CI_WIRE_END = "# SV_GATE: proof_registry_excludes_gates (v1) end"

PROVE_CI_WIRE_BLOCK = f"""\
{PROVE_CI_WIRE_BEGIN}
bash scripts/gate_proof_surface_registry_excludes_gates_v1.sh
{PROVE_CI_WIRE_END}
"""


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _insert_or_replace_block(text: str, begin: str, end: str, block: str) -> str:
    if begin in text and end in text:
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
        out = pattern.sub(block.strip(), text, count=1)
        return out if out.endswith("\n") else out + "\n"
    out = text.rstrip() + "\n\n" + block.strip() + "\n"
    return out


def _ensure_gate_script() -> None:
    _ensure_parent(GATE)

    gate_text = """#!/usr/bin/env bash
set -euo pipefail

# SquadVault — gate: Proof Surface Registry excludes gates (v1)
#
# Canonical rule:
#   CI gates (scripts/gate_*.sh) are enforcement and MUST NOT appear in the Proof Surface Registry.
#
# This gate fails CI if any scripts/gate_*.sh reference is present in:
#   docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
#
# CWD independence: resolve repo root from this script's location.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REG="${REPO_ROOT}/docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
if [[ ! -f "${REG}" ]]; then
  echo "ERROR: missing proof surface registry: ${REG}" >&2
  exit 2
fi

# Reject any reference to gate scripts in the registry.
# Keep this intentionally narrow and high-signal.
if grep -nE 'scripts/gate_[A-Za-z0-9_]+\\.sh' "${REG}" >/dev/null; then
  echo "ERROR: Proof Surface Registry must not reference CI gates (scripts/gate_*.sh)." >&2
  echo "Offending lines:" >&2
  grep -nE 'scripts/gate_[A-Za-z0-9_]+\\.sh' "${REG}" >&2 || true
  exit 1
fi

exit 0
"""
    if GATE.exists():
        if _read(GATE) != gate_text:
            _write(GATE, gate_text)
    else:
        _write(GATE, gate_text)
    GATE.chmod(0o755)


def _wire_into_prove_ci() -> None:
    if not PROVE_CI.exists():
        raise SystemExit(f"ERROR: missing {PROVE_CI}")

    txt = _read(PROVE_CI)

    # Replace if already present (idempotent)
    if PROVE_CI_WIRE_BEGIN in txt and PROVE_CI_WIRE_END in txt:
        pattern = re.compile(re.escape(PROVE_CI_WIRE_BEGIN) + r".*?" + re.escape(PROVE_CI_WIRE_END), re.DOTALL)
        txt2 = pattern.sub(PROVE_CI_WIRE_BLOCK.strip(), txt, count=1)
        _write(PROVE_CI, txt2 if txt2.endswith("\n") else txt2 + "\n")
        return

    # Canonical anchor (substring-based): wire immediately after the line that invokes the CWD-independence shims gate.
    anchor_substr = "gate_cwd_independence_shims_v1.sh"
    lines = txt.splitlines(keepends=True)

    for i, line in enumerate(lines):
        if anchor_substr in line:
            insert_at = i + 1
            block = PROVE_CI_WIRE_BLOCK.strip() + "\n"
            # Insert a single blank line first if next line is non-blank
            if insert_at < len(lines) and lines[insert_at].strip() != "":
                block = "\n" + block
            lines.insert(insert_at, block)
            out = "".join(lines)
            _write(PROVE_CI, out if out.endswith("\n") else out + "\n")
            return

    raise SystemExit(
        f"ERROR: could not find anchor substring `{anchor_substr}` in scripts/prove_ci.sh; refusing to patch."
    )


def _update_docs() -> None:
    if not DOC_PROOF_REGISTRY.exists():
        raise SystemExit(f"ERROR: missing {DOC_PROOF_REGISTRY}")
    if not DOC_GUARDRAILS_INDEX.exists():
        raise SystemExit(f"ERROR: missing {DOC_GUARDRAILS_INDEX}")

    reg = _read(DOC_PROOF_REGISTRY)
    reg2 = _insert_or_replace_block(reg, DOC_RULE_BEGIN, DOC_RULE_END, DOC_RULE_BLOCK)
    _write(DOC_PROOF_REGISTRY, reg2)

    idx = _read(DOC_GUARDRAILS_INDEX)
    idx2 = _insert_or_replace_block(idx, INDEX_ENTRY_BEGIN, INDEX_ENTRY_END, INDEX_ENTRY_BLOCK)
    _write(DOC_GUARDRAILS_INDEX, idx2)


def main() -> None:
    _ensure_gate_script()
    _wire_into_prove_ci()
    _update_docs()
    print("OK: patched proof registry boundary + enforcement gate (v1)")


if __name__ == "__main__":
    main()
