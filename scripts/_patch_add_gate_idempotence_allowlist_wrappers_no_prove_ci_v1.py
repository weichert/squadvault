from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh"

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

# Gate: idempotence allowlist wrappers must not recurse into prove_ci (v1)
#
# Reads: scripts/patch_idempotence_allowlist_v1.txt (blank lines and #comments ignored)
# For each wrapper:
#   - ensure file exists
#   - fail if it contains an *unguarded* `bash scripts/prove_ci.sh` invocation
#
# Conservative check:
#   - detect lines containing `bash (./)?scripts/prove_ci.sh`
#   - for each match, require `SV_IDEMPOTENCE_MODE` to appear "nearby" (±20 lines)
#     otherwise fail and print offending lines.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ALLOWLIST="${REPO_ROOT}/scripts/patch_idempotence_allowlist_v1.txt"
if [[ ! -f "${ALLOWLIST}" ]]; then
  echo "ERROR: allowlist not found: ${ALLOWLIST}" >&2
  exit 1
fi

wrappers=()
while IFS= read -r line; do
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "${line}" ]] && continue
  [[ "${line}" == \#* ]] && continue
  wrappers+=("${line}")
done < "${ALLOWLIST}"

if [[ "${#wrappers[@]}" -eq 0 ]]; then
  echo "ERROR: allowlist is empty after filtering comments/blanks: ${ALLOWLIST}" >&2
  exit 1
fi

fail=0
prove_pat='\\bbash[[:space:]]+(\\./)?scripts/prove_ci\\.sh\\b'

for rel in "${wrappers[@]}"; do
  p="${REPO_ROOT}/${rel}"
  if [[ ! -f "${p}" ]]; then
    echo "ERROR: allowlisted wrapper missing: ${rel}" >&2
    fail=1
    continue
  fi

  mapfile -t lines < "${p}"

  matches=()
  for i in "${!lines[@]}"; do
    if echo "${lines[$i]}" | grep -Eq "${prove_pat}"; then
      matches+=("$i")
    fi
  done

  if [[ "${#matches[@]}" -eq 0 ]]; then
    continue
  fi

  for idx in "${matches[@]}"; do
    start=$(( idx - 20 ))
    end=$(( idx + 20 ))
    (( start < 0 )) && start=0
    (( end >= ${#lines[@]} )) && end=$(( ${#lines[@]} - 1 ))

    found_guard=0
    for j in $(seq "${start}" "${end}"); do
      if echo "${lines[$j]}" | grep -q 'SV_IDEMPOTENCE_MODE'; then
        found_guard=1
        break
      fi
    done

    if [[ "${found_guard}" -ne 1 ]]; then
      echo "ERROR: unguarded prove_ci invocation detected in allowlisted wrapper:" >&2
      echo "  wrapper: ${rel}" >&2
      echo "  offending line: $((idx+1)):${lines[$idx]}" >&2
      echo "  rule: any 'bash scripts/prove_ci.sh' must be guarded by SV_IDEMPOTENCE_MODE nearby (±20 lines)" >&2
      fail=1
    fi
  done
done

if [[ "${fail}" -ne 0 ]]; then
  exit 1
fi

echo "OK: idempotence allowlist wrappers do not recurse into prove_ci (guarded)"
"""

def main() -> int:
  GATE.parent.mkdir(parents=True, exist_ok=True)

  if GATE.exists():
    existing = GATE.read_text(encoding="utf-8")
    if existing == GATE_TEXT:
      return 0
    raise SystemExit(f"REFUSE: {GATE} exists but content differs (manual edit?)")

  GATE.write_text(GATE_TEXT, encoding="utf-8")
  return 0

if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except SystemExit:
    raise
  except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    raise SystemExit(1)
