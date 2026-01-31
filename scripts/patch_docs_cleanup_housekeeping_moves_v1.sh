#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: docs cleanup moves (v1) ==="

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

need_file() {
  local p="$1"
  if [[ ! -f "$p" ]]; then
    echo "ERROR: expected file missing: $p" >&2
    exit 2
  fi
}

# --- Archive legacy contract-card DOCX now superseded by canonical MD ---
mkdir -p docs/90_archive/contract_cards_docx

need_file docs/30_contract_cards/ops/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx
git mv docs/30_contract_cards/ops/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx \
      docs/90_archive/contract_cards_docx/

need_file docs/30_contract_cards/ops/TONE_ENGINE_Contract_Card_v1.0.docx
git mv docs/30_contract_cards/ops/TONE_ENGINE_Contract_Card_v1.0.docx \
      docs/90_archive/contract_cards_docx/

# --- Delete promoted asset duplicates still lingering in _import/VENDOR ---
dup_paths=(
  "docs/_import/VENDOR/2026-01-28_batch2/SquadVault_Build_Phase_Sprint_1_First_Engineering_Sprint_Plan_v1.0.pdf"
  "docs/_import/VENDOR/2026-01-28_batch2/SquadVault_DesignKey_Labeled_v1_June2025.png"
  "docs/_import/VENDOR/2026-01-28_batch2/SquadVault_LeaguePhoto_2019_Framed.png"
)

for p in "${dup_paths[@]}"; do
  need_file "${p}"
  git rm -f "${p}"
done

echo "OK: staged moves/removals"
git status --porcelain=v1
echo "OK"
