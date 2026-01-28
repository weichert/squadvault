#!/usr/bin/env bash
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "$*" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT="${1:-SquadVault_Claude_Independent_Review_Pack_2026-01-28.zip}"

REQUIRED_FILES=(
  "docs/40_specs/architecture/SquadVault_Phase_1_Architecture_Complete.docx"
  "docs/SquadVault_Documentation_Map_v1.5.docx"
  "docs/50_ops_and_build/SquadVault_Development_Playbook_MVP_v1.1.docx"
  "docs/50_ops_and_build/SquadVault_Implementation_Readiness_Package_IRP_v1.0.docx"
  "docs/50_ops_and_build/SquadVault_Technical_Diligence_Companion_v1.0.docx"
  "docs/50_ops_and_build/SquadVault_AI_Development_Rules_of_Engagement_v1.0.docx"
  "docs/50_ops_and_build/SquadVault_Stop_Before_Suggesting_X_Guardrails_v1.0.docx"
  "docs/50_ops_and_build/SquadVault_What_We_Are_Not_Platform_Guardrails_v1.0.docx"
)

# Optional: include if present in this repo checkout; otherwise we warn and continue.
OPTIONAL_FILES=(
  "docs/40_specs/SquadVault_Core_Engine_Technical_Specification_v1.0.docx"
)

log "==> verifying REQUIRED inputs (exist + non-zero)"
for f in "${REQUIRED_FILES[@]}"; do
  [ -f "$f" ] || die "missing file: $f"
  sz="$(stat -f%z "$f" 2>/dev/null || true)"
  [ -n "$sz" ] || die "could not stat: $f"
  [ "$sz" -gt 0 ] || die "0-byte file: $f"
done

ZIP_FILES=("${REQUIRED_FILES[@]}")

log "==> checking OPTIONAL inputs"
for f in "${OPTIONAL_FILES[@]}"; do
  if [ -f "$f" ]; then
    sz="$(stat -f%z "$f" 2>/dev/null || true)"
    if [ -z "$sz" ] || [ "$sz" -le 0 ]; then
      die "optional file exists but is not readable/non-zero: $f"
    fi
    log "OK: optional included: $f"
    ZIP_FILES+=("$f")
  else
    log "WARN: optional missing (skipping): $f"
  fi
done

log "==> building zip: $OUT"
rm -f "$OUT"
# -q quiet, -X strip extra attributes for reproducibility-ish
zip -q -X "$OUT" "${ZIP_FILES[@]}" || die "zip failed"

log "==> zip contents"
unzip -l "$OUT" || die "unzip -l failed"

log "OK: wrote $OUT"
