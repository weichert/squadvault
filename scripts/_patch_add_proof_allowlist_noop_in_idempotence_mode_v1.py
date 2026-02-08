from __future__ import annotations

from pathlib import Path

PROOF = Path("scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh")
PROVE_CI = Path("scripts/prove_ci.sh")
REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")
OPS_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

ALLOWLIST = Path("scripts/patch_idempotence_allowlist_v1.txt")

PROOF_TEXT = """#!/usr/bin/env bash
# SquadVault — proof: allowlist wrappers no-op under SV_IDEMPOTENCE_MODE=1 (v1)
#
# Proves:
#   - Every wrapper listed in scripts/patch_idempotence_allowlist_v1.txt produces no repo mutations
#     when invoked with SV_IDEMPOTENCE_MODE=1 from a clean tree.
#
# Constraints:
#   - repo-root anchored
#   - bash3-safe
#   - deterministic
#   - idempotent (does not mutate repo)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

require_clean() {
  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "ERROR: repo must be clean: ${1}"
    git status --porcelain=v1
    exit 2
  fi
}

require_file() {
  if [[ ! -f "${1}" ]]; then
    echo "ERROR: missing required file: ${1}"
    exit 2
  fi
}

echo "==> Proof: allowlisted patch wrappers are no-op under SV_IDEMPOTENCE_MODE=1 (v1)"

require_file "scripts/patch_idempotence_allowlist_v1.txt"
require_clean "entry"

count=0
while IFS= read -r raw; do
  line="${raw}"
  line="$(echo "${line}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  if [[ -z "${line}" ]]; then
    continue
  fi
  if [[ "${line}" == \#* ]]; then
    continue
  fi

  if [[ ! -f "${line}" ]]; then
    echo "ERROR: allowlist wrapper not found: ${line}"
    exit 2
  fi
  if [[ ! -x "${line}" ]]; then
    echo "ERROR: allowlist wrapper not executable: ${line}"
    exit 2
  fi

  count=$((count + 1))
  echo "==> [${count}] ${line}"
  SV_IDEMPOTENCE_MODE=1 bash "${line}"

  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "ERROR: wrapper mutated repo under SV_IDEMPOTENCE_MODE=1: ${line}"
    echo "==> git status --porcelain=v1"
    git status --porcelain=v1
    echo "==> git diff --name-only"
    git diff --name-only || true
    exit 2
  fi
done < "scripts/patch_idempotence_allowlist_v1.txt"

echo "==> wrappers checked: ${count}"
require_clean "exit"
echo "OK"
"""

def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True

def patch_prove_ci() -> bool:
    if not PROVE_CI.exists():
        raise SystemExit(f"ERROR: missing {PROVE_CI}")

    text = PROVE_CI.read_text(encoding="utf-8")

    call = "bash scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh"
    if call in text:
        return False

    # Insert after the idempotence gate allowlist v1 if present (best locality).
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and ("gate_patch_wrapper_idempotence_allowlist_v1.sh" in line):
            out.append("\n")
            out.append('echo "==> Proof: allowlisted patch wrappers are no-op under SV_IDEMPOTENCE_MODE=1"\n')
            out.append(f"{call}\n")
            inserted = True

    if not inserted:
        # Conservative fallback: append near end.
        out.append("\n")
        out.append('echo "==> Proof: allowlisted patch wrappers are no-op under SV_IDEMPOTENCE_MODE=1"\n')
        out.append(f"{call}\n")

    PROVE_CI.write_text("".join(out), encoding="utf-8")
    return True

def patch_registry() -> bool:
    if not REGISTRY.exists():
        raise SystemExit(f"ERROR: missing {REGISTRY}")
    text = REGISTRY.read_text(encoding="utf-8")

    entry = "- `scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh` — Allowlisted patch wrappers are no-op under `SV_IDEMPOTENCE_MODE=1`.\n"
    if entry in text:
        return False

    begin = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
    end = "<!-- CI_PROOF_RUNNERS_END -->"

    if begin in text and end in text:
        pre, rest = text.split(begin, 1)
        mid, post = rest.split(end, 1)
        if entry in mid:
            return False
        mid2 = mid
        if not mid2.endswith("\n"):
            mid2 += "\n"
        mid2 += entry
        REGISTRY.write_text(pre + begin + mid2 + end + post, encoding="utf-8")
        return True

    # Backward compatible: insert under heading.
    heading = "## Proof Runners"
    if heading not in text:
        raise SystemExit("ERROR: missing '## Proof Runners' in registry doc (and markers absent).")

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and (line.strip() == heading):
            out.append("\n")
            out.append(entry)
            inserted = True
    REGISTRY.write_text("".join(out), encoding="utf-8")
    return True

def patch_ops_index() -> bool:
    if not OPS_INDEX.exists():
        raise SystemExit(f"ERROR: missing {OPS_INDEX}")
    text = OPS_INDEX.read_text(encoding="utf-8")

    marker = "prove_idempotence_allowlist_noop_in_idempotence_mode_v1"
    if marker in text:
        return False

    line = "- `scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh` — Allowlisted patch wrappers are no-op under `SV_IDEMPOTENCE_MODE=1`.\n"

    anchors = ["## Proofs", "## CI Proofs", "## Proof Surface"]
    anchor = next((a for a in anchors if a in text), None)

    if anchor is None:
        OPS_INDEX.write_text(text + "\n## Proofs\n\n" + line, encoding="utf-8")
        return True

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = False
    for l in lines:
        out.append(l)
        if (not inserted) and (l.strip() == anchor):
            out.append("\n")
            out.append(line)
            inserted = True
    OPS_INDEX.write_text("".join(out), encoding="utf-8")
    return True

def main() -> None:
    changed = False
    changed |= write_if_changed(PROOF, PROOF_TEXT)
    changed |= patch_prove_ci()
    changed |= patch_registry()
    changed |= patch_ops_index()

    if changed:
        print("OK: added proof + wired into prove_ci + updated docs (v1).")
    else:
        print("OK: proof + wiring + docs already canonical (v1).")

if __name__ == "__main__":
    main()
