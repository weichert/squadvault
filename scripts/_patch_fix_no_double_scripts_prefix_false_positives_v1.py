from __future__ import annotations

from pathlib import Path

GATE_V2 = Path("scripts/gate_no_double_scripts_prefix_v2.sh")
GATE_V1 = Path("scripts/gate_no_double_scripts_prefix_v1.sh")
INS_WRAPPER_V2 = Path("scripts/patch_prove_ci_insert_under_docs_gates_anchor_v2.sh")

EXPECTED_GATE_V2 = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Scan tracked bash entrypoints:
# - prove scripts
# - gate scripts
# - patch wrappers
#
# IMPORTANT: only flag *actual invocations* of a doubly-prefixed path, not
# guardrail scripts that mention the pattern in their own grep checks.
#
# We flag lines like:
#   bash scripts/scripts/<...>
#   ./scripts/scripts/<...>

scan_globs=(
  "scripts/prove_*.sh"
  "scripts/gate_*.sh"
  "scripts/patch_*.sh"
)

found_any=0

for g in "${scan_globs[@]}"; do
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    test -f "${f}"

    # bad: bash scripts/scripts/...
    if grep -nE '^[[:space:]]*bash[[:space:]]+scripts/scripts/' "${f}" >/dev/null; then
      echo "ERROR: detected forbidden double scripts prefix invocation in ${f}"
      grep -nE '^[[:space:]]*bash[[:space:]]+scripts/scripts/' "${f}" || true
      found_any=1
    fi

    # bad: ./scripts/scripts/...
    if grep -nE '^[[:space:]]*\\./scripts/scripts/' "${f}" >/dev/null; then
      echo "ERROR: detected forbidden double scripts prefix invocation in ${f}"
      grep -nE '^[[:space:]]*\\./scripts/scripts/' "${f}" || true
      found_any=1
    fi
  done < <(git ls-files "${g}")
done

if [[ "${found_any}" -ne 0 ]]; then
  exit 1
fi

echo "OK: no double scripts prefix invocations found."
"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")

def _patch_gate_v1(s: str) -> str:
    # Replace literal "scripts/scripts/" pattern with a concatenation to avoid tripping v2.
    # Keep behavior identical.
    if "scripts/scripts/" not in s:
        return s

    # Ensure we only change the grep patterns, not prose.
    s = s.replace('grep -nF "scripts/scripts/"', 'DOUBLE="scripts/""scripts/"; grep -nF "${DOUBLE}"')
    s = s.replace('if grep -nF "scripts/scripts/"', 'DOUBLE="scripts/""scripts/"; if grep -nF "${DOUBLE}"')
    s = s.replace('echo "ERROR: detected forbidden \'scripts/scripts/\'', 'echo "ERROR: detected forbidden double scripts prefix')

    return s

def _patch_insert_wrapper_v2(s: str) -> str:
    # Avoid literal "bash scripts/scripts/" token in the wrapper itself.
    if "bash scripts/scripts/" not in s:
        return s
    # Replace the grep needle with a concatenation.
    return s.replace(
        'if grep -nF "bash scripts/scripts/" scripts/prove_ci.sh >/dev/null; then',
        'BAD="bash scripts/""scripts/"; if grep -nF "${BAD}" scripts/prove_ci.sh >/dev/null; then',
    )

def main() -> None:
    for p in (GATE_V2, GATE_V1, INS_WRAPPER_V2):
        if not p.exists():
            _refuse(f"missing required file: {p}")

    # 1) gate v2: make it invocation-aware
    existing_v2 = _read(GATE_V2)
    if existing_v2 != EXPECTED_GATE_V2 and existing_v2 != (EXPECTED_GATE_V2 + "\n"):
        # Overwrite to canonical (this is a gate; we want exact contents)
        _write(GATE_V2, EXPECTED_GATE_V2)

    # 2) gate v1: remove literal scripts/scripts/ token (keep semantics)
    s1 = _read(GATE_V1)
    s1n = _patch_gate_v1(s1)
    if s1n != s1:
        _write(GATE_V1, s1n)

    # 3) insertion wrapper v2: remove literal bash scripts/scripts/ token (keep semantics)
    sw = _read(INS_WRAPPER_V2)
    swn = _patch_insert_wrapper_v2(sw)
    if swn != sw:
        _write(INS_WRAPPER_V2, swn)

if __name__ == "__main__":
    main()
