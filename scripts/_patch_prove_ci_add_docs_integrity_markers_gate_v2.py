from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
GATE = Path("scripts/gate_docs_integrity_markers_v2.sh")

ANCHOR = "SV_ANCHOR: docs_gates (v1)"

INSERT_BLOCK = """\
# SV_GATE: docs_integrity_markers (v2) begin
echo "==> Docs integrity markers gate (v2)"
bash scripts/gate_docs_integrity_markers_v2.sh
# SV_GATE: docs_integrity_markers (v2) end
"""

GATE_TEXT = """#!/usr/bin/env bash
# SquadVault — Docs Integrity Markers Gate (v2)
#
# Enforces that canonical docs/index marker blocks exist exactly once.
#
# Constraints:
#   - bash3-safe
#   - deterministic
#   - does NOT depend on git dirty/clean state
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

need_file_tracked_or_present() {
  local path="$1"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files --error-unmatch "$path" >/dev/null 2>&1 || fail "required tracked file missing: $path"
  else
    [[ -f "$path" ]] || fail "required file missing (no git): $path"
  fi
}

count_fixed() {
  local needle="$1"
  local path="$2"
  local c
  c="$(grep -F -c -- "$needle" "$path" 2>/dev/null || true)"
  echo "${c}"
}

echo "==> Docs integrity markers gate (v2)"

CI_INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
need_file_tracked_or_present "$CI_INDEX"

m1="<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->"
m2="<!-- SV_DOCS_MUTATION_GUARDRAIL_GATE: v2 (v1) -->"

c1="$(count_fixed "$m1" "$CI_INDEX")"
c2="$(count_fixed "$m2" "$CI_INDEX")"

[[ "$c1" == "1" ]] || fail "marker must appear exactly once (found $c1): $m1"
[[ "$c2" == "1" ]] || fail "marker must appear exactly once (found $c2): $m2"

echo "OK: docs integrity markers gate passed (v2)."
"""

def _write_if_diff(path: Path, text: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _insert_under_anchor(text: str, anchor: str, block: str) -> str:
    if block in text:
        return text
    lines = text.splitlines(True)
    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and (anchor in ln):
            out.append("\n")
            out.append(block)
            out.append("\n")
            inserted = True
    if not inserted:
        raise SystemExit(f"anchor not found in {PROVE}: {anchor}")
    return "".join(out)

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")

    # 1) Write gate script
    _write_if_diff(GATE, GATE_TEXT)

    # 2) Wire into prove_ci
    prove_text = PROVE.read_text(encoding="utf-8")
    new_text = _insert_under_anchor(prove_text, ANCHOR, INSERT_BLOCK)
    if new_text != prove_text:
        PROVE.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
