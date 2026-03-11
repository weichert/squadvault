from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
RULES = Path("docs/process/rules_of_engagement.md")

GATE_V2 = Path("scripts/gate_docs_mutation_guardrail_v2.sh")

# --- prove_ci wiring ---
OLD_BLOCK = """\
# SV_GATE: docs_mutation_guardrail (v1) begin
echo "==> Docs mutation guardrail gate"
bash scripts/gate_docs_mutation_guardrail_v1.sh
# SV_GATE: docs_mutation_guardrail (v1) end
"""

NEW_BLOCK = """\
# SV_GATE: docs_mutation_guardrail (v2) begin
echo "==> Docs mutation guardrail gate"
bash scripts/gate_docs_mutation_guardrail_v2.sh
# SV_GATE: docs_mutation_guardrail (v2) end
"""

ANCHOR = "SV_ANCHOR: docs_gates (v1)"

# --- CI index canonical discoverability block (must appear exactly once) ---
MARKER_LINE = "<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->"
BULLET_LINE = "- docs/process/rules_of_engagement.md — Docs + CI Mutation Policy (Enforced)"

CANON_BLOCK = f"""\

{MARKER_LINE}
{BULLET_LINE}
"""

GATE_V2_TEXT = """#!/usr/bin/env bash
# SquadVault — Docs Mutation Guardrail Gate (v2)
#
# v2 hardening:
#   - Marker-based enforcement for CI index discoverability (stable to rewording).
#   - Requires exactly one canonical discoverability block for rules_of_engagement.
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

need_grep_fixed() {
  local needle="$1"
  local path="$2"
  grep -F -q -- "$needle" "$path" || fail "missing required text in $path: $needle"
}

count_fixed() {
  # prints count of fixed-string matches (as a number)
  local needle="$1"
  local path="$2"
  # grep -c exits 1 if 0 matches; normalize
  local c
  c="$(grep -F -c -- "$needle" "$path" 2>/dev/null || true)"
  echo "${c}"
}

echo "==> Docs mutation guardrail gate (v2)"

RULES_DOC="docs/process/rules_of_engagement.md"
CI_INDEX_DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

need_file_tracked_or_present "$RULES_DOC"
need_file_tracked_or_present "$CI_INDEX_DOC"

# Rules-of-engagement must carry the enforced policy section (stable anchor)
need_grep_fixed "## Docs + CI Mutation Policy (Enforced)" "$RULES_DOC"
need_grep_fixed "scripts/_patch_" "$RULES_DOC"
need_grep_fixed "scripts/patch_" "$RULES_DOC"

# CI index must contain canonical marker + bullet exactly once
marker="<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->"
bullet="- docs/process/rules_of_engagement.md — Docs + CI Mutation Policy (Enforced)"

mcount="$(count_fixed "$marker" "$CI_INDEX_DOC")"
bcount="$(count_fixed "$bullet" "$CI_INDEX_DOC")"

[[ "$mcount" == "1" ]] || fail "CI index marker must appear exactly once (found $mcount): $marker"
[[ "$bcount" == "1" ]] || fail "CI index bullet must appear exactly once (found $bcount): $bullet"

# Canonical patcher/wrapper example must exist
need_file_tracked_or_present "scripts/_patch_example_noop_v1.py"
need_file_tracked_or_present "scripts/patch_example_noop_v1.sh"

echo "OK: docs mutation guardrail gate passed (v2)."
"""

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _write_if_diff(path: Path, text: str) -> None:
    if path.exists() and _read(path) == text:
        return
    _write(path, text)

def _dedupe_ci_index(text: str) -> str:
    # Remove ALL occurrences of marker + bullet lines (anywhere), then append canonical block once.
    lines = text.splitlines(True)
    out: list[str] = []
    for ln in lines:
        if MARKER_LINE in ln:
            continue
        if BULLET_LINE in ln:
            continue
        out.append(ln)

    new_text = "".join(out)
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text += CANON_BLOCK
    return new_text

def _rewrite_prove_ci(text: str) -> str:
    if NEW_BLOCK in text:
        return text

    if OLD_BLOCK in text:
        return text.replace(OLD_BLOCK, NEW_BLOCK)

    # If v1 block not found, insert v2 under anchor (fallback)
    lines = text.splitlines(True)
    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and (ANCHOR in ln):
            out.append("\n")
            out.append(NEW_BLOCK)
            out.append("\n")
            inserted = True
    if not inserted:
        raise SystemExit(f"anchor not found in {PROVE}: {ANCHOR}")
    return "".join(out)

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")
    if not CI_INDEX.exists():
        raise SystemExit(f"missing canonical file: {CI_INDEX}")
    if not RULES.exists():
        raise SystemExit(f"missing canonical file: {RULES}")

    # 1) Write gate v2
    _write_if_diff(GATE_V2, GATE_V2_TEXT)

    # 2) Dedupe + canonicalize CI index discoverability block
    ci_text = _read(CI_INDEX)
    ci_new = _dedupe_ci_index(ci_text)
    if ci_new != ci_text:
        _write(CI_INDEX, ci_new)

    # 3) Rewire prove_ci to call v2 gate
    prove_text = _read(PROVE)
    prove_new = _rewrite_prove_ci(prove_text)
    if prove_new != prove_text:
        _write(PROVE, prove_new)

if __name__ == "__main__":
    main()
