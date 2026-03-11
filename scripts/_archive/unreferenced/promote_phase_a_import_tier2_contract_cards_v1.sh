#!/usr/bin/env bash
set -euo pipefail
echo "=== Phase A: import Tier-2 contract cards into docs/30_contract_cards/ops (v1) ==="

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/promote_phase_a_import_tier2_contract_cards_v1.sh [--apply]

Defaults:
  - Dry-run only. Use --apply to execute.
  - Fail-closed:
      * all source files must exist
      * no destination overwrites
USAGE
}

APPLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: Unknown arg: $1"; echo; usage; exit 2 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

SRC_BASE="/Users/steve/Library/Mobile Documents/com~apple~CloudDocs/Steve/Projects/SquadVault/Data Ingestion/squadvault-ingest/docs/contracts/tier_2"
DST_DIR="docs/30_contract_cards/ops"

mkdir -p "${DST_DIR}"

src_tone="${SRC_BASE}/tone_engine/tone_engine_contract_v1.0.docx"
src_approval="${SRC_BASE}/approval_authority/approval_authority_contract_v1.0.docx"
src_version_nav="${SRC_BASE}/version_presentation_navigation/version_presentation_navigation_contract_v1.0.docx"
src_eal_calibration="${SRC_BASE}/eal_calibration/eal_calibration_contract_v1.0.docx"
src_validation_strategy="${SRC_BASE}/contract_validation_strategy/contract_validation_strategy_contract_v1.0.docx"

dst_tone="${DST_DIR}/TONE_ENGINE_Contract_Card_v1.0.docx"
dst_approval="${DST_DIR}/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx"
dst_version_nav="${DST_DIR}/VERSION_PRESENTATION_NAVIGATION_Contract_Card_v1.0.docx"
dst_eal_calibration="${DST_DIR}/EAL_CALIBRATION_Contract_Card_v1.0.docx"
dst_validation_strategy="${DST_DIR}/CONTRACT_VALIDATION_STRATEGY_Contract_Card_v1.0.docx"

# sources must exist
for p in "${src_tone}" "${src_approval}" "${src_version_nav}" "${src_eal_calibration}" "${src_validation_strategy}"; do
  if [[ ! -f "${p}" ]]; then
    echo "ERROR: missing source: ${p}"
    exit 2
  fi
done

# refuse overwrite
for d in "${dst_tone}" "${dst_approval}" "${dst_version_nav}" "${dst_eal_calibration}" "${dst_validation_strategy}"; do
  if [[ -e "${d}" ]]; then
    echo "ERROR: destination exists (refusing to overwrite): ${d}"
    exit 2
  fi
done

echo
echo "Planned copies (source -> destination):"
printf "  %s -> %s\n" "${src_tone}" "${dst_tone}"
printf "  %s -> %s\n" "${src_approval}" "${dst_approval}"
printf "  %s -> %s\n" "${src_version_nav}" "${dst_version_nav}"
printf "  %s -> %s\n" "${src_eal_calibration}" "${dst_eal_calibration}"
printf "  %s -> %s\n" "${src_validation_strategy}" "${dst_validation_strategy}"
echo

if [[ "${APPLY}" -eq 0 ]]; then
  echo "DRY-RUN: no files copied."
  echo "Re-run with --apply to execute."
  exit 0
fi

# copy (not move) so we don't depend on iCloud being stable for provenance
cp -f "${src_tone}" "${dst_tone}"
cp -f "${src_approval}" "${dst_approval}"
cp -f "${src_version_nav}" "${dst_version_nav}"
cp -f "${src_eal_calibration}" "${dst_eal_calibration}"
cp -f "${src_validation_strategy}" "${dst_validation_strategy}"

echo "OK: imported Tier-2 contract cards into ${DST_DIR}"
