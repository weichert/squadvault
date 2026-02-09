from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

CANON = """#!/usr/bin/env bash
set -euo pipefail

echo "==> Gate: CI Guardrails ops entrypoints parity (v1)"

DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
PROVE="scripts/prove_ci.sh"

if [[ ! -f "${DOC}" ]]; then
  echo "ERROR: missing ${DOC}" >&2
  exit 2
fi
if [[ ! -f "${PROVE}" ]]; then
  echo "ERROR: missing ${PROVE}" >&2
  exit 2
fi

# Extract the bounded entrypoints section from the ops index.
# We only consider gate scripts (scripts/gate_*.sh).
indexed="$(
  awk '
    BEGIN { in=0 }
    /SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN/ { in=1; next }
    /SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END/   { in=0; exit }
    in { print }
  ' "${DOC}" \
  | grep -oE 'scripts/gate_[A-Za-z0-9_]+\\.sh' \
  | sort -u
)"

# Extract executed gate scripts from prove_ci.
# This counts:
#   - bash scripts/gate_x.sh ...
#   - scripts/gate_x.sh ...
#   - VAR="$(scripts/gate_x.sh begin)"
# but ignores commented lines.
executed="$(
  grep -vE '^\\s*#' "${PROVE}" \
    | grep -oE 'scripts/gate_[A-Za-z0-9_]+\\.sh' \
    | sort -u
)"

# Compare sets (comm requires sorted input).
missing="$(
  comm -23 <(printf "%s\\n" "${indexed}") <(printf "%s\\n" "${executed}") || true
)"
extra="$(
  comm -13 <(printf "%s\\n" "${indexed}") <(printf "%s\\n" "${executed}") || true
)"

rc=0

if [[ -n "${missing}" ]]; then
  echo
  echo "==== Indexed (bounded) but NOT executed (fail) ===="
  echo "${missing}"
  rc=1
fi

if [[ -n "${extra}" ]]; then
  echo
  echo "==== Executed but NOT indexed (fail) ===="
  echo "${extra}"
  rc=1
fi

if [[ "${rc}" -ne 0 ]]; then
  echo
  echo "ERROR: CI guardrails ops entrypoint parity gate failed."
  exit 1
fi

echo
echo "OK: ops index ↔ prove_ci gate entrypoints parity (v1)."
"""

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not GATE.exists():
        die(f"missing {GATE}")

    cur = GATE.read_text(encoding="utf-8")
    if cur == CANON:
        return
    GATE.write_text(CANON, encoding="utf-8")

if __name__ == "__main__":
    main()
