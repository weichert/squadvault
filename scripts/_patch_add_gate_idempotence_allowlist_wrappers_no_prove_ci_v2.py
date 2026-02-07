from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh"

GATE_TEXT_BASH32_SAFE = """#!/usr/bin/env bash
set -euo pipefail

# Gate: idempotence allowlist wrappers must not recurse into prove_ci (v1)
#
# Reads: scripts/patch_idempotence_allowlist_v1.txt (blank lines and #comments ignored)
# For each wrapper:
#   - ensure file exists
#   - fail if it contains an *unguarded* `bash scripts/prove_ci.sh` invocation
#
# Conservative check (bash 3.2 compatible; no mapfile):
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

  prove_lines="$(grep -nE "${prove_pat}" "${p}" || true)"
  [[ -z "${prove_lines}" ]] && continue

  guard_lines="$(grep -n 'SV_IDEMPOTENCE_MODE' "${p}" || true)"

  while IFS= read -r hit; do
    [[ -z "${hit}" ]] && continue
    hit_ln="${hit%%:*}"
    hit_txt="${hit#*:}"

    found_guard=0
    if [[ -n "${guard_lines}" ]]; then
      while IFS= read -r g; do
        [[ -z "${g}" ]] && continue
        g_ln="${g%%:*}"
        if [[ "${g_ln}" -ge "$((hit_ln - 20))" && "${g_ln}" -le "$((hit_ln + 20))" ]]; then
          found_guard=1
          break
        fi
      done <<< "${guard_lines}"
    fi

    if [[ "${found_guard}" -ne 1 ]]; then
      echo "ERROR: unguarded prove_ci invocation detected in allowlisted wrapper:" >&2
      echo "  wrapper: ${rel}" >&2
      echo "  offending line: ${hit_ln}:${hit_txt}" >&2
      echo "  rule: any 'bash scripts/prove_ci.sh' must be guarded by SV_IDEMPOTENCE_MODE nearby (±20 lines)" >&2
      fail=1
    fi
  done <<< "${prove_lines}"
done

if [[ "${fail}" -ne 0 ]]; then
  exit 1
fi

echo "OK: idempotence allowlist wrappers do not recurse into prove_ci (guarded)"
"""

def main() -> int:
    GATE.parent.mkdir(parents=True, exist_ok=True)

    if GATE.exists():
        current = GATE.read_text(encoding="utf-8")
        if current == GATE_TEXT_BASH32_SAFE:
            return 0

        # Strict safety: only overwrite if it looks like the intended gate.
        if "idempotence allowlist wrappers must not recurse into prove_ci" not in current:
            raise SystemExit(f"REFUSE: {GATE} exists but does not look like expected gate; won't overwrite")

    GATE.write_text(GATE_TEXT_BASH32_SAFE, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
