from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
GATE = Path("scripts/check_python_shim_compliance_v1.sh")

# Anchor: we insert immediately after this line if present.
ANCHOR_NEEDLE = "== CI Proof Suite =="

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

echo "==> Python shim compliance gate"

# This gate enforces the Ops Shim & CWD Independence contract:
# - repo-related Python execution must go through scripts/py
# - avoid python/python3 direct invocation patterns in operator flows
#
# Scope: scripts/ + docs/
# Exclusions: venvs, node_modules, .git, dist/build artifacts, cache dirs

die() {
  echo "ERROR: $*" >&2
  exit 1
}

note() {
  echo "NOTE: $*" >&2
}

# Resolve repo root relative to this script (CWD-independent)
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
repo_root="$(cd -- "${here}/.." >/dev/null 2>&1 && pwd)"

cd "${repo_root}"

# Grep helper: return 0 if matches exist, else 1
has_matches() {
  local pattern="$1"
  shift || true
  # Using grep (not rg) per repo conventions
  grep -R -n -E "${pattern}" "$@" >/dev/null 2>&1
}

# Print matches (bounded to scoped dirs)
print_matches() {
  local pattern="$1"
  shift || true
  grep -R -n -E "${pattern}" "$@" || true
}

# Scoped roots
SCOPED_DIRS=(scripts docs)

# Exclusions (grep -R lacks a perfect exclude set; we keep scope narrow instead)
# We still avoid scanning extracted blobs if they exist.
EXTRACTED_HINTS=(
  "docs/30_contract_cards"
  "docs/**/_extracted_txt"
)

# Forbidden patterns:
#  - direct python/python3 calls (especially to scripts/*)
#  - PYTHONPATH injection
# Allowed:
#  - docs text may mention "scripts/py" (good)
#  - non-repo python usage is not expected in scripts/ or docs/
FORBIDDEN=(
  '(^|[^A-Za-z0-9_])(python3|python)([[:space:]]+|$)'
  '(^|[^A-Za-z0-9_])PYTHONPATH='
)

# Allowlist patterns (we ignore matches that are clearly referencing the shim itself)
ALLOWLIST=(
  '(^|[^A-Za-z0-9_])scripts/py([^A-Za-z0-9_]|$)'
  '(^|[^A-Za-z0-9_])\./scripts/py([^A-Za-z0-9_]|$)'
)

# Collect violations with a conservative approach:
# If a line contains forbidden AND does NOT contain an allowlist marker, flag it.
violations=0

for pat in "${FORBIDDEN[@]}"; do
  # Search only in scoped dirs.
  if has_matches "${pat}" "${SCOPED_DIRS[@]}"; then
    # Print candidates, then filter out allowlisted references.
    candidates="$(print_matches "${pat}" "${SCOPED_DIRS[@]}")"
    if [ -n "${candidates}" ]; then
      # Filter: drop lines that contain allowlist markers.
      filtered="${candidates}"
      for ok in "${ALLOWLIST[@]}"; do
        filtered="$(printf "%s\n" "${filtered}" | grep -v -E "${ok}" || true)"
      done

      if [ -n "${filtered}" ]; then
        echo "FAIL: detected forbidden Python invocation patterns (must use scripts/py):" >&2
        echo "" >&2
        printf "%s\n" "${filtered}" >&2
        echo "" >&2
        echo "Remediation:" >&2
        echo "  - Replace python/python3 invocations with: ./scripts/py <args>" >&2
        echo "  - Remove PYTHONPATH=... usage; shims must establish import context" >&2
        echo "  - For operator examples in docs, show ./scripts/py or ./scripts/recap.sh" >&2
        violations=1
      fi
    fi
  fi
done

if [ "${violations}" -ne 0 ]; then
  exit 1
fi

echo "OK: Python shim compliance gate passed."
"""

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSAL: {msg}")

def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing {PROVE}")

    # 1) Ensure gate file exists with exact content if absent.
    if not GATE.exists():
        GATE.write_text(GATE_TEXT, encoding="utf-8")
    else:
        # If present, do not overwrite; refuse if it looks like a different gate.
        existing = GATE.read_text(encoding="utf-8")
        if "Python shim compliance gate" not in existing:
            _refuse(f"{GATE} exists but does not look like the expected gate (missing marker).")

    # Ensure executable bit handled by wrapper (we avoid chmod here for portability).

    # 2) Wire into prove_ci.sh exactly once.
    txt = PROVE.read_text(encoding="utf-8")
    if "check_python_shim_compliance_v1" in txt or "check_python_shim_compliance_v1.sh" in txt:
        return  # already wired

    if ANCHOR_NEEDLE not in txt:
        _refuse(f"could not find anchor needle in {PROVE}: {ANCHOR_NEEDLE!r}")

    lines = txt.splitlines(True)
    out: list[str] = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and (ANCHOR_NEEDLE in line):
            out.append("\n")
            out.append("echo \"==> Python shim compliance gate\"\n")
            out.append("./scripts/check_python_shim_compliance_v1.sh\n")
            out.append("\n")
            inserted = True

    if not inserted:
        _refuse("failed to insert wiring block (unexpected).")

    PROVE.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
