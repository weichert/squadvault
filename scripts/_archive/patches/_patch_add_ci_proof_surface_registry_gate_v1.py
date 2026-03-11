from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Proof_Surface_Registry_v1.0.md"
GATE = REPO_ROOT / "scripts" / "check_ci_proof_surface_matches_registry_v1.sh"

REGISTRY_CONTENT = """\
[SV_CANONICAL_HEADER_V1]
Contract Name: CI Proof Surface Registry
Version: v1.0
Status: CANONICAL — FROZEN

Defers To:
  - SquadVault — Canonical Operating Constitution (Tier 0)
  - SquadVault — Ops Shim & CWD Independence Contract (Ops)
  - SquadVault Development Playbook (MVP)

Default: Any behavior not explicitly permitted by this registry is forbidden.

—

# SquadVault — CI Proof Surface Registry (v1.0)

## FROZEN DECLARATION (ENFORCED)

This registry defines the **complete, authoritative CI proof surface**.

**FROZEN:** CI may run only the proofs listed here. Any drift (addition/removal/rename) must:
1) update this registry via versioned patcher + wrapper, and
2) pass the enforcement gate.

This registry is intentionally boring and auditable.

## CI Entrypoint (GitHub Actions invokes this)

- scripts/prove_ci.sh — Single blessed CI entrypoint; runs gates + invokes all proof runners below.

## Proof Runners (invoked by scripts/prove_ci.sh)

- scripts/prove_eal_calibration_type_a_v1.sh — Proves EAL calibration Type A invariants end-to-end.
- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates.
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh — Proves Rivalry Chronicle generate → approve → export flow.
- scripts/prove_signal_scout_tier1_type_a_v1.sh — Proves Signal Scout Tier-1 Type A derivation + determinism.
- scripts/prove_tone_engine_type_a_v1.sh — Proves Tone Engine Type A contract/invariants.
- scripts/prove_version_presentation_navigation_type_a_v1.sh — Proves version presentation + navigation invariants.

## Notes

- **No globbing. No discovery. No heuristics.**
- The enforcement gate compares this registry against **exact proof invocations in `scripts/prove_ci.sh`**.
"""

GATE_SCRIPT_CONTENT = """\
#!/usr/bin/env bash
set -euo pipefail

# === CI Proof Surface Registry Gate (v1) ===
# Fail closed. No heuristics. No globbing.

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
    if [[ "${line}" =~ ^-\ (scripts/prove_[A-Za-z0-9_]+\.sh)\ —\  ]]; then
      path="${BASH_REMATCH[1]}"
      registry_list+="${path}"$'\n'
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

# normalize + ensure uniqueness
registry_sorted="$(printf "%s" "${registry_list}" | sed '/^$/d' | LC_ALL=C sort)"
registry_uniq="$(printf "%s\n" "${registry_sorted}" | LC_ALL=C uniq)"
if [[ "$(printf "%s\n" "${registry_sorted}" | wc -l | tr -d ' ')" != "$(printf "%s\n" "${registry_uniq}" | wc -l | tr -d ' ')" ]]; then
  echo "ERROR: registry contains duplicate proof runner entries." >&2
  exit 1
fi

# --- Parse prove_ci.sh: extract strict proof invocations; fail if any 'prove_' line is nonconforming ---
ci_list=""
bad_lines=0
while IFS= read -r line; do
  if [[ "${line}" == *prove_* ]]; then
    # strict allowed forms (no args):
    #   bash scripts/prove_x.sh
    #   ./scripts/prove_x.sh
    #   scripts/prove_x.sh
    if [[ "${line}" =~ ^[[:space:]]*(bash[[:space:]]+)?(\./)?(scripts/prove_[A-Za-z0-9_]+\.sh)[[:space:]]*$ ]]; then
      ci_list+="${BASH_REMATCH[3]}"$'\n'
    else
      echo "ERROR: nonconforming proof invocation in scripts/prove_ci.sh (fail-closed):" >&2
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
ci_uniq="$(printf "%s\n" "${ci_sorted}" | LC_ALL=C uniq)"

# Compare sets
extra_in_ci="$(comm -13 <(printf "%s\n" "${registry_uniq}") <(printf "%s\n" "${ci_uniq}") || true)"
extra_in_registry="$(comm -23 <(printf "%s\n" "${registry_uniq}") <(printf "%s\n" "${ci_uniq}") || true)"

if [[ -n "${extra_in_ci}" ]]; then
  echo "ERROR: CI invokes proof(s) not listed in registry:" >&2
  printf "%s\n" "${extra_in_ci}" >&2
  exit 1
fi

if [[ -n "${extra_in_registry}" ]]; then
  echo "ERROR: Registry lists proof(s) not invoked by CI:" >&2
  printf "%s\n" "${extra_in_registry}" >&2
  exit 1
fi

echo "OK: CI proof surface matches registry (v1)."
"""

INSERT_BLOCK = """\
# ==> Gate: CI proof surface registry (v1)
bash scripts/check_ci_proof_surface_matches_registry_v1.sh
"""

def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")

def _write_text(path: Path, text: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding="utf-8")

def _insert_gate_into_prove_ci(src: str) -> str:
  if "check_ci_proof_surface_matches_registry_v1.sh" in src:
    return src  # idempotent

  lines = src.splitlines(keepends=True)

  # Preferred anchor: after the CI proof-suite banner marker.
  marker = "== CI Proof Suite =="
  for i, ln in enumerate(lines):
    if marker in ln:
      lines.insert(i + 1, INSERT_BLOCK if INSERT_BLOCK.endswith("\n") else INSERT_BLOCK + "\n")
      return "".join(lines)

  # Fallback anchor: insert immediately before the first strict proof runner invocation line.
  import re
  pat = re.compile(r"^[ \t]*(bash[ \t]+)?(\./)?(scripts/prove_[A-Za-z0-9_]+\.sh)[ \t]*$", re.M)
  for i, ln in enumerate(lines):
    if pat.match(ln.rstrip("\n")):
      lines.insert(i, INSERT_BLOCK if INSERT_BLOCK.endswith("\n") else INSERT_BLOCK + "\n")
      return "".join(lines)

  raise SystemExit(
    "ERROR: could not find insertion anchor in scripts/prove_ci.sh "
    "(expected '== CI Proof Suite ==' or a strict 'scripts/prove_*.sh' invocation line)"
  )

def main() -> None:
  if not PROVE_CI.exists():
    raise SystemExit(f"ERROR: missing {PROVE_CI}")

  # Ensure registry exists (create if missing)
  if not REGISTRY.exists():
    _write_text(REGISTRY, REGISTRY_CONTENT)

  # Ensure gate exists (create if missing)
  if not GATE.exists():
    _write_text(GATE, GATE_SCRIPT_CONTENT)

  # Patch prove_ci.sh
  src = _read_text(PROVE_CI)
  new_src = _insert_gate_into_prove_ci(src)
  if new_src != src:
    _write_text(PROVE_CI, new_src)

if __name__ == "__main__":
  main()
