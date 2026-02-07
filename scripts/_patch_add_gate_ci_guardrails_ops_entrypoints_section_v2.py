from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh")

EXPECTED = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: CI Guardrails ops entrypoints section + TOC (v2) ==="

DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

BEGIN_SECTION="<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->"
END_SECTION="<!-- SV_END: ops_entrypoints_hub (v1) -->"

BEGIN_TOC="<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->"
END_TOC="<!-- SV_END: ops_entrypoints_toc (v1) -->"

test -f "${DOC}"

extract_bounded() {
  local begin="$1"
  local end="$2"
  local out

  out="$(
    awk -v b="${begin}" -v e="${end}" '
      $0 == b {p=1}
      p {print}
      $0 == e {exit}
    ' "${DOC}"
  )"

  if [[ -z "${out}" ]]; then
    echo "ERROR: missing bounded section in ${DOC}"
    echo "  begin=${begin}"
    echo "  end=${end}"
    exit 1
  fi

  echo "${out}"
}

toc="$(extract_bounded "${BEGIN_TOC}" "${END_TOC}")"
section="$(extract_bounded "${BEGIN_SECTION}" "${END_SECTION}")"

# TOC must include the anchor entry
echo "${toc}" | grep -F "[Ops Entrypoints (Canonical)](#ops-entrypoints-canonical)" >/dev/null

# Main bounded section must include the required links
echo "${section}" | grep -F "Ops_Entrypoints_Hub_v1.0.md" >/dev/null
echo "${section}" | grep -F "Canonical_Indices_Map_v1.0.md" >/dev/null
echo "${section}" | grep -F "Process_Discipline_Index_v1.0.md" >/dev/null
echo "${section}" | grep -F "Recovery_Workflows_Index_v1.0.md" >/dev/null
echo "${section}" | grep -F "Ops_Rules_One_Page_v1.0.md" >/dev/null
echo "${section}" | grep -F "New_Contributor_Orientation_10min_v1.0.md" >/dev/null

echo "OK: ops entrypoints bounded section + TOC entry present + complete."
"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def main() -> None:
    if TARGET.exists():
        existing = _read(TARGET)
        if existing != EXPECTED and existing != (EXPECTED + "\n"):
            _refuse(f"{TARGET} exists but does not match expected canonical contents.")
        return

    _write(TARGET, EXPECTED)


if __name__ == "__main__":
    main()
