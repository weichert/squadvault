from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "check_ci_proof_surface_matches_registry_v1.sh"

NEW_CONTENT = """\
#!/usr/bin/env bash
set -euo pipefail

# === CI Proof Surface Registry Gate (v1) ===
# Fail closed. No heuristics. No globbing.
#
# v1 enforcement scope:
# - Enforce the SET of proof-runner scripts invoked by scripts/prove_ci.sh matches the registry.
# - Do NOT constrain proof runner arguments/env in v1 (existing CI behavior must not change).

script_path="${BASH_SOURCE[0]-}"
if [[ -z "${script_path}" ]]; then
  echo "ERROR: run as a script file: bash scripts/check_ci_proof_surface_matches_registry_v1.sh" >&2
  exit 1
fi

self_dir="$(cd "$(dirname "${script_path}")" && pwd)"
repo_root="$(cd "${self_dir}/.." && pwd)"

registry="${repo_root}/docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
prove_ci="${repo_root}/scripts/prove_ci.sh"

if [[ ! -f "${registry}" ]]; then
  echo "ERROR: registry missing: ${registry}" >&2
  exit 1
fi
if [[ ! -f "${prove_ci}" ]]; then
  echo "ERROR: prove_ci missing: ${prove_ci}" >&2
  exit 1
fi

# --- Parse registry: only the Proof Runners section ---
in_section=0
registry_list=""
while IFS= read -r line; do
  if [[ "${line}" == "## Proof Runners (invoked by scripts/prove_ci.sh)" ]]; then
    in_section=1
    continue
  fi
  if [[ "${line}" == "## "* ]]; then
    if [[ "${in_section}" -eq 1 ]]; then
      in_section=0
    fi
  fi
  if [[ "${in_section}" -eq 1 ]]; then
    # required format: "- scripts/prove_...sh — purpose"
    if [[ "${line}" =~ ^-\ (scripts/prove_[A-Za-z0-9_]+\\.sh)\ —\  ]]; then
      path="${BASH_REMATCH[1]}"
      registry_list+="${path}"$'\\n'
    elif [[ "${line}" =~ ^-\  ]]; then
      echo "ERROR: registry entry malformed (expected '- scripts/prove_*.sh — ...'):" >&2
      echo "  ${line}" >&2
      exit 1
    fi
  fi
done < "${registry}"

if [[ -z "${registry_list}" ]]; then
  echo "ERROR: registry Proof Runners section is empty or missing." >&2
  exit 1
fi

registry_sorted="$(printf "%s" "${registry_list}" | sed '/^$/d' | LC_ALL=C sort)"
registry_uniq="$(printf "%s\\n" "${registry_sorted}" | LC_ALL=C uniq)"
if [[ "$(printf "%s\\n" "${registry_sorted}" | wc -l | tr -d ' ')" != "$(printf "%s\\n" "${registry_uniq}" | wc -l | tr -d ' ')" ]]; then
  echo "ERROR: registry contains duplicate proof runner entries." >&2
  exit 1
fi

# --- Parse prove_ci.sh: extract invoked proof scripts ---
#
# We only count direct invocations of scripts/prove_*.sh.
# Allowed command forms (with optional env/args/continuations):
#   [ENV=... ]* (bash )? (./)? scripts/prove_x.sh [args...] [\\]
#
# We ignore:
# - comments
# - references inside conditionals (if/elif/while/until) to avoid counting help-probes as "invocations".
#
ci_list=""
bad_lines=0

while IFS= read -r line; do
  # ignore comments + blanks
  if [[ "${line}" =~ ^[[:space:]]*# ]]; then
    continue
  fi
  if [[ "${line}" =~ ^[[:space:]]*$ ]]; then
    continue
  fi

  # ignore conditional headers (fail-closed for set enforcement: they are not "invocations")
  if [[ "${line}" =~ ^[[:space:]]*(if|elif|while|until)[[:space:]] ]]; then
    continue
  fi

  # If the line contains a prove script token, it must match our explicit allowed invocation grammar.
  if [[ "${line}" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*((bash)[[:space:]]+)?(\\./)?(scripts/prove_[A-Za-z0-9_]+\\.sh)([[:space:]]|$|\\\\) ]]; then
    # optional ENV assignments, optional 'bash', optional './', then scripts/prove_*.sh, then anything (args), optional trailing backslash
    if [[ "${line}" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*((bash)[[:space:]]+)?(\\./)?(scripts/prove_[A-Za-z0-9_]+\\.sh)([[:space:]].*)?$ ]]; then
      ci_list+="${BASH_REMATCH[5]}"$'\\n'
    else
      echo "ERROR: nonconforming proof invocation line in scripts/prove_ci.sh (fail-closed):" >&2
      echo "  ${line}" >&2
      bad_lines=1
    fi
  fi
done < "${prove_ci}"

if [[ "${bad_lines}" -ne 0 ]]; then
  exit 1
fi

if [[ -z "${ci_list}" ]]; then
  echo "ERROR: no proof invocations found in scripts/prove_ci.sh." >&2
  exit 1
fi

ci_sorted="$(printf "%s" "${ci_list}" | sed '/^$/d' | LC_ALL=C sort)"
ci_uniq="$(printf "%s\\n" "${ci_sorted}" | LC_ALL=C uniq)"

extra_in_ci="$(comm -13 <(printf "%s\\n" "${registry_uniq}") <(printf "%s\\n" "${ci_uniq}") || true)"
extra_in_registry="$(comm -23 <(printf "%s\\n" "${registry_uniq}") <(printf "%s\\n" "${ci_uniq}") || true)"

if [[ -n "${extra_in_ci}" ]]; then
  echo "ERROR: CI invokes proof(s) not listed in registry:" >&2
  printf "%s\\n" "${extra_in_ci}" >&2
  exit 1
fi

if [[ -n "${extra_in_registry}" ]]; then
  echo "ERROR: Registry lists proof(s) not invoked by CI:" >&2
  printf "%s\\n" "${extra_in_registry}" >&2
  exit 1
fi

echo "OK: CI proof surface matches registry (v1)."
"""

def main() -> None:
  if not GATE.exists():
    raise SystemExit(f"ERROR: missing {GATE}")
  GATE.write_text(NEW_CONTENT, encoding="utf-8")

if __name__ == "__main__":
  main()
