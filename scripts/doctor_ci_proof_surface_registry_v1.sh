#!/usr/bin/env bash
set -euo pipefail

echo "=== Doctor: CI Proof Surface Registry (v1) ==="

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  echo "FAIL: not inside a git repo (cannot locate repo root)." >&2
  exit 1
fi
cd "${REPO_ROOT}"

REG="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"

MODE="${1:-check}"
if [[ "${MODE}" != "check" && "${MODE}" != "fix" ]]; then
  echo "FAIL: usage:" >&2
  echo "  $0 check   # diagnose only" >&2
  echo "  $0 fix     # attempt safe repairs" >&2
  exit 2
fi

if [[ ! -f "${REG}" ]]; then
  echo "FAIL: missing ${REG}" >&2
  exit 1
fi

echo "==> [1] Locate bounded blocks"
if ! grep -n "SV_PROOF_SURFACE_LIST_v1_BEGIN\|SV_PROOF_SURFACE_LIST_v1_END\|CI_PROOF_RUNNERS_BEGIN\|CI_PROOF_RUNNERS_END" "${REG}" >/dev/null; then
  echo "FAIL: missing required markers in registry" >&2
  exit 1
fi
echo "OK: markers present"

echo "==> [2] Check CI_PROOF_RUNNERS strict bullet grammar"
bad_runner_lines="$(
  awk '
    $0 ~ /CI_PROOF_RUNNERS_BEGIN/ {flag=1; next}
    $0 ~ /CI_PROOF_RUNNERS_END/   {flag=0}
    flag==1 {print}
  ' "${REG}"   | sed '/^[[:space:]]*$/d'   | sed '/^[[:space:]]*<!--.*-->[[:space:]]*$/d'   | awk '
      # strict bullet: - scripts/prove_...sh — description
      $0 ~ /^-[[:space:]]+scripts\/prove_[A-Za-z0-9_]+\.sh[[:space:]]+—[[:space:]]+/ {next}
      {print}
    '
)"

if [[ -n "${bad_runner_lines}" ]]; then
  echo "ERROR: CI_PROOF_RUNNERS contains nonconforming line(s):" >&2
  printf "%s\n" "${bad_runner_lines}" | sed 's/^/  - /' >&2
  if [[ "${MODE}" == "fix" ]]; then
    echo "==> Fix mode: fail-closed. Ambiguous lines left untouched." >&2
    echo "    Use the register wrapper to add proper descriptions." >&2
  else
    exit 1
  fi
else
  echo "OK: CI_PROOF_RUNNERS grammar is strict"
fi

echo "==> [3] Check Surface List is sorted + unique"
surface_paths="$(
  awk '
    $0 ~ /SV_PROOF_SURFACE_LIST_v1_BEGIN/ {flag=1; next}
    $0 ~ /SV_PROOF_SURFACE_LIST_v1_END/   {flag=0}
    flag==1 {print}
  ' "${REG}" | sed '/^[[:space:]]*$/d'
)"

dups="$(printf "%s\n" "${surface_paths}" | LC_ALL=C sort | uniq -d || true)"
if [[ -n "${dups}" ]]; then
  echo "ERROR: Surface List has duplicates:" >&2
  printf "%s\n" "${dups}" | sed 's/^/  - /' >&2
  [[ "${MODE}" == "fix" ]] || exit 1
fi

sorted="$(printf "%s\n" "${surface_paths}" | LC_ALL=C sort)"
if [[ "${sorted}" != "${surface_paths}" ]]; then
  echo "ERROR: Surface List is not sorted (LC_ALL=C)." >&2
  [[ "${MODE}" == "fix" ]] || exit 1
  echo "==> Fix: re-sort Surface List block (safe)"
  python - <<'PYS'
from pathlib import Path
REG=Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")
BEGIN="<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->"
END="<!-- SV_PROOF_SURFACE_LIST_v1_END -->"
s=REG.read_text(encoding="utf-8")
pre, rest = s.split(BEGIN,1)
mid, post = rest.split(END,1)
lines=[ln.strip() for ln in mid.splitlines() if ln.strip()]
out="\n"+"\n".join(sorted(set(lines)))+"\n"
REG.write_text(pre+BEGIN+out+END+post, encoding="utf-8")
print("OK: Surface List re-sorted + uniqued.")
PYS
else
  echo "OK: Surface List sorted + unique"
fi

echo "==> [4] Run canonical registry↔CI checker"
bash scripts/check_ci_proof_surface_matches_registry_v1.sh
echo "OK: checker PASS"

echo "OK: doctor complete (${MODE})."
