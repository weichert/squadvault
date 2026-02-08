from __future__ import annotations

from pathlib import Path

PROVE_CI = Path("scripts/prove_ci.sh")
PROOF = Path("scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh")

GATE_CALL = "bash scripts/gate_no_terminal_banner_paste_v1.sh"
PROOF_CALL = "bash scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh"
PROOF_ECHO = 'echo "==> Proof: terminal banner paste gate behavior (v1)"'

HINT = 'echo "NOTE: If you just created new patcher/wrapper files, commit them before running prove_ci."'
HINT_BLOCK = f"""if [[ "${{sv_clean}}" != "CLEAN" ]]; then
  {HINT}
fi
"""

PROOF_TEXT = """#!/usr/bin/env bash
# SquadVault — proof: terminal banner paste gate behavior (v1)
#
# What this proves:
#  1) Strict mode fails when a *tracked* scripts/*.txt contains a real banner line.
#  2) Anchoring prevents false positives from pattern-literal text (e.g., \"'^Last login: '\").
#  3) Escape hatch SV_ALLOW_TERMINAL_BANNER_PASTE=1 exits 0 and emits WARN.
#
# Determinism:
#  - Requires clean repo at entry.
#  - Temporarily stages a synthetic file, runs gate, then fully cleans up.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof requires clean repo (working tree + index)."
  git status --porcelain=v1
  exit 2
fi

TMP="scripts/.sv_tmp_terminal_banner_probe_v1.txt"

cleanup() {
  set +e
  git reset -q -- "${TMP}" >/dev/null 2>&1
  rm -f "${TMP}"
  set -e
}
trap cleanup EXIT

# --- Case 1: strict mode should FAIL on a tracked banner line ---
cat > "${TMP}" <<'EOF'
Last login: Fri Feb  6 23:41:20 on ttys061
EOF

git add "${TMP}"

set +e
out="$(bash scripts/gate_no_terminal_banner_paste_v1.sh 2>&1)"
rc=$?
set -e

if [[ $rc -eq 0 ]]; then
  echo "ERROR: expected gate to fail in strict mode when banner line is present."
  echo "${out}"
  exit 1
fi

git reset -q -- "${TMP}"
rm -f "${TMP}"

# --- Case 2: anchored patterns should NOT match pattern-literal text ---
cat > "${TMP}" <<'EOF'
  '^Last login: '
EOF

git add "${TMP}"

bash scripts/gate_no_terminal_banner_paste_v1.sh

git reset -q -- "${TMP}"
rm -f "${TMP}"

# --- Case 3: escape hatch should WARN + exit 0 ---
set +e
out2="$(SV_ALLOW_TERMINAL_BANNER_PASTE=1 bash scripts/gate_no_terminal_banner_paste_v1.sh 2>&1)"
rc2=$?
set -e

if [[ $rc2 -ne 0 ]]; then
  echo "ERROR: expected escape hatch to exit 0."
  echo "${out2}"
  exit 1
fi

echo "${out2}" | grep -n "WARN:" >/dev/null

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof left repo dirty unexpectedly."
  git status --porcelain=v1
  exit 1
fi

echo "OK: terminal banner gate behavior proved (v1)."
"""

def ensure_proof_script() -> None:
    if PROOF.exists() and PROOF.read_text(encoding="utf-8") == PROOF_TEXT:
        print("OK: proof script already canonical (v1).")
        return
    PROOF.write_text(PROOF_TEXT, encoding="utf-8")
    print("OK: wrote proof script (v1).")

def wire_proof_into_prove_ci(lines: list[str]) -> list[str]:
    joined = "".join(lines)
    if PROOF_CALL in joined:
        print("OK: prove_ci already wires banner proof (idempotent).")
        return lines

    for i, line in enumerate(lines):
        if line.strip() == GATE_CALL:
            block = [
                f"{GATE_CALL}\n",
                f"{PROOF_ECHO}\n",
                f"{PROOF_CALL}\n",
            ]
            print("OK: wired banner proof after banner gate in prove_ci.sh")
            return lines[:i] + block + lines[i + 1 :]

    raise SystemExit("ERROR: could not find exact banner gate call line in prove_ci.sh to wire proof.")

def add_hint_after_sv_clean(lines: list[str]) -> list[str]:
    joined = "".join(lines)
    if HINT in joined:
        print("OK: dirty-repo hint already present (idempotent).")
        return lines

    # Anchor: insert right after the sv_clean computation line that references porcelain=v1.
    # This is stable (you showed grep hits at line ~107).
    anchor = 'git status --porcelain=v1'
    for i, line in enumerate(lines):
        if anchor in line and "sv_clean" in line:
            print("OK: inserted dirty-repo hint after sv_clean computation")
            return lines[: i + 1] + [HINT_BLOCK] + lines[i + 1 :]

    raise SystemExit("ERROR: could not locate sv_clean porcelain line to insert hint.")

def main() -> None:
    if not PROVE_CI.exists():
        raise SystemExit(f"ERROR: missing {PROVE_CI}")

    ensure_proof_script()

    lines = PROVE_CI.read_text(encoding="utf-8").splitlines(keepends=True)
    lines = wire_proof_into_prove_ci(lines)
    lines = add_hint_after_sv_clean(lines)

    PROVE_CI.write_text("".join(lines), encoding="utf-8")
    print("OK: wrote updated prove_ci.sh")

if __name__ == "__main__":
    main()
