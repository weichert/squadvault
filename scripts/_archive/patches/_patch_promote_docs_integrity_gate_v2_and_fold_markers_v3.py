from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
GATE_V2 = Path("scripts/gate_docs_integrity_v2.sh")

ANCHOR = "SV_ANCHOR: docs_gates (v1)"

MARKERS_BEGIN = "# SV_GATE: docs_integrity_markers (v2) begin"
MARKERS_END = "# SV_GATE: docs_integrity_markers (v2) end"

V2_BLOCK = """\
# SV_GATE: docs_integrity (v2) begin
echo "==> Docs integrity gate (v2)"
bash scripts/gate_docs_integrity_v2.sh
# SV_GATE: docs_integrity (v2) end
"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def _write_if_diff(p: Path, s: str) -> None:
    if p.exists() and _read(p) == s:
        return
    _write(p, s)

def _discover_docs_integrity_v1_script(prove_text: str) -> str:
    # Ground truth: prove_ci currently invokes docs integrity via prove_docs_integrity_v1.sh.
    # Discover that path without guessing.
    for line in prove_text.splitlines():
        s = line.strip()
        if not s.startswith("bash "):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        path = parts[1]
        if path.startswith("scripts/prove_docs_integrity") and path.endswith(".sh"):
            return path
    raise SystemExit("could not discover docs integrity v1 script (expected bash scripts/prove_docs_integrity*.sh)")

def _remove_markers_gate_block(lines: list[str]) -> list[str]:
    out: list[str] = []
    skipping = False
    for ln in lines:
        if MARKERS_BEGIN in ln:
            skipping = True
            continue
        if skipping:
            if MARKERS_END in ln:
                skipping = False
            continue
        out.append(ln)
    return out

def _remove_existing_v2_block(text: str) -> str:
    # If our v2 block already exists, no-op.
    if V2_BLOCK in text:
        return text
    return text

def _insert_v2_under_anchor(lines: list[str]) -> list[str]:
    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and (ANCHOR in ln):
            out.append("\n")
            out.append(V2_BLOCK)
            out.append("\n")
            inserted = True
    if not inserted:
        raise SystemExit(f"anchor not found in {PROVE}: {ANCHOR}")
    return out

def _gate_v2_text(v1_script: str) -> str:
    return f"""#!/usr/bin/env bash
# SquadVault — Docs Integrity Gate (v2)
#
# v2 = existing docs integrity proof + marker exact-once enforcement (folded).
#
# Constraints:
#   - bash3-safe
#   - deterministic
#   - does NOT depend on git dirty/clean state
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
REPO_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
cd "${{REPO_ROOT}}"

fail() {{
  echo "FAIL: $*" >&2
  exit 1
}}

need_file_tracked_or_present() {{
  local path="$1"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files --error-unmatch "$path" >/dev/null 2>&1 || fail "required tracked file missing: $path"
  else
    [[ -f "$path" ]] || fail "required file missing (no git): $path"
  fi
}}

count_fixed() {{
  local needle="$1"
  local path="$2"
  local c
  c="$(grep -F -c -- "$needle" "$path" 2>/dev/null || true)"
  echo "${{c}}"
}}

echo "==> Docs integrity gate (v2)"

# 1) Baseline docs integrity proof
bash "{v1_script}"

# 2) Marker exact-once enforcement (folded from docs_integrity_markers gate v2)
CI_INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
need_file_tracked_or_present "$CI_INDEX"

m1="<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->"
m2="<!-- SV_DOCS_MUTATION_GUARDRAIL_GATE: v2 (v1) -->"

c1="$(count_fixed "$m1" "$CI_INDEX")"
c2="$(count_fixed "$m2" "$CI_INDEX")"

[[ "$c1" == "1" ]] || fail "marker must appear exactly once (found $c1): $m1"
[[ "$c2" == "1" ]] || fail "marker must appear exactly once (found $c2): $m2"

echo "OK: docs integrity gate passed (v2)."
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")

    prove_text = _read(PROVE)
    v1_script = _discover_docs_integrity_v1_script(prove_text)

    # 1) Write v2 gate
    _write_if_diff(GATE_V2, _gate_v2_text(v1_script))

    # 2) Remove markers gate block from prove_ci
    lines = prove_text.splitlines(True)
    lines2 = _remove_markers_gate_block(lines)

    # 3) Insert v2 gate block under anchor (idempotent)
    text2 = "".join(lines2)
    text2 = _remove_existing_v2_block(text2)
    if V2_BLOCK not in text2:
        lines3 = text2.splitlines(True)
        lines4 = _insert_v2_under_anchor(lines3)
        text3 = "".join(lines4)
    else:
        text3 = text2

    if text3 != prove_text:
        _write(PROVE, text3)

if __name__ == "__main__":
    main()
