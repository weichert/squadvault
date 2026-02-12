#!/usr/bin/env bash
# SquadVault — prove creative determinism (v1)
#
# Goal:
#   Detect silent drift in exported creative assemblies across identical runs.
#
# Scope:
#   This v1 proof is intentionally conservative:
#   - It treats the "export assemblies" output surface as the canonical drift boundary.
#   - It does NOT attempt to force model-level determinism; it detects drift in the repo's
#     exported assembly artifacts and refuses silent changes.
#
# Contract alignment:
#   - Facts are immutable; narratives are derived
#   - Silence is valid; drift is forbidden unless explicitly versioned
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Bash3-safe mktemp usage (macOS compatible)
tmp_root="${TMPDIR:-/tmp}"
WORK="$(mktemp -d "${tmp_root%/}/sv_creative_drift_v1.XXXXXX")"
trap 'rm -rf "${WORK}"' EXIT

cd "${REPO_ROOT}"

# Candidate output roots (we avoid inventing new ones).
# We only hash what exists.
CANDIDATES=(
  "out"
  "exports"
  "export"
  "artifacts"
  ".sv"
  "tmp"
)

existing=()
for d in "${CANDIDATES[@]}"; do
  if [[ -d "${REPO_ROOT}/${d}" ]]; then
    existing+=("${d}")
  fi
done

if [[ "${#existing[@]}" -eq 0 ]]; then
  echo "ERROR: No known output directories found to hash for drift detection." >&2
  echo "Searched: ${CANDIDATES[*]}" >&2
  echo "Fix: Create/standardize a canonical export output dir (out/ or exports/) and re-run." >&2
  exit 2
fi

echo "==> Drift guard will hash these output roots:"
for d in "${existing[@]}"; do
  echo "  - ${d}"
done

hash_tree() {
  # Hash all files under the selected output roots deterministically.
  # - Exclude .git always
  # - Exclude obvious caches (best effort)
  # - Stable ordering via sort
  local dest="$1"
  : > "${dest}"

  for root in "${existing[@]}"; do
    # Find regular files only
    # shellcheck disable=SC2016
    find "${REPO_ROOT}/${root}" -type f \
      ! -path "*/.git/*" \
      ! -path "*/__pycache__/*" \
      ! -name "*.pyc" \
      -print \
    | sort \
    | while IFS= read -r f; do
        # Prefer shasum if present, else fallback to python
        if command -v shasum >/dev/null 2>&1; then
          shasum -a 256 "${f}" >> "${dest}"
        else
          python="${PYTHON:-python}"
          "${python}" - <<PY >> "${dest}"
import hashlib, sys
p = sys.argv[1]
h = hashlib.sha256()
with open(p,"rb") as fh:
    while True:
        b = fh.read(1024*1024)
        if not b: break
        h.update(b)
print(h.hexdigest(), p)
PY
        fi
      done
  done
}

clean_outputs() {
  # IMPORTANT: Only delete inside known output roots, never elsewhere.
  for root in "${existing[@]}"; do
    # Keep directories, remove files.
# --- SV_PRESERVE_CREATIVE_FINGERPRINT_ON_CLEAN_OUTPUTS_v1_BEGIN ---
    fingerprint_rel="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"
    fingerprint_abs="${REPO_ROOT}/${fingerprint_rel}"

    # Keep directories, remove files — but preserve the tracked canonical fingerprint.
    if [[ "${root}" == "artifacts" ]]; then
      find "${REPO_ROOT}/${root}" -type f \
        ! -path "${fingerprint_abs}" \
        -print0 | xargs -0 rm -f
    else
      find "${REPO_ROOT}/${root}" -type f -print0 | xargs -0 rm -f
    fi
# --- SV_PRESERVE_CREATIVE_FINGERPRINT_ON_CLEAN_OUTPUTS_v1_END ---
  done
}

run_golden_path_from() {
  local cwd="$1"
  (
    cd "${cwd}"
    # Golden path already encodes canonical operator flow and should be CWD-independent.
    # We do not pass extra env knobs here; this is a drift detector, not a behavior mutator.
    bash "${REPO_ROOT}/scripts/prove_golden_path.sh"
  )
}

echo "==> (A) Clean outputs and run golden path from repo root"
clean_outputs
run_golden_path_from "${REPO_ROOT}"
hash_tree "${WORK}/hash_A.txt"

echo "==> (B) Clean outputs and run golden path from non-repo CWD"
clean_outputs
run_golden_path_from "${WORK}"
hash_tree "${WORK}/hash_B.txt"

echo "==> Compare drift hashes"
if ! diff -u "${WORK}/hash_A.txt" "${WORK}/hash_B.txt" >/dev/null 2>&1; then
  echo "ERROR: Creative/export drift detected between identical runs." >&2
  echo "---- diff (A vs B) ----" >&2
  diff -u "${WORK}/hash_A.txt" "${WORK}/hash_B.txt" || true
  echo "-----------------------" >&2
  echo "Policy: silent drift is forbidden. Fix export determinism or version outputs explicitly." >&2
  exit 1
fi

echo "OK: No drift detected (creative/export surface stable across CWD + rerun)."
