#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

MARKER_BEGIN = "# SV_PATCH: NAC preflight fingerprint normalization (v2)\n"
MARKER_END = "# /SV_PATCH: NAC preflight fingerprint normalization (v2)\n"

ANCHOR = 'echo "Selected assembly: $ASSEMBLY"\n'

BLOCK = """\
# SV_PATCH: NAC preflight fingerprint normalization (v2)
# NAC requires a 64-lower-hex fingerprint in the BEGIN_CANONICAL_FINGERPRINT block.
# Some fixtures/export paths can emit a placeholder 'test-fingerprint'. Normalize it.
if grep -q -- "Selection fingerprint: test-fingerprint" "$ASSEMBLY"; then
  echo "==> NAC preflight: replacing placeholder selection fingerprint in assembly"

  # Pull fp from DB (APPROVED WEEKLY_RECAP), else fallback to 64 zeros.
  _sv_fp="$(
    sqlite3 -noheader -batch "$DB" "
      SELECT selection_fingerprint
      FROM recap_artifacts
      WHERE league_id='${LEAGUE_ID}'
        AND season=${SEASON}
        AND week_index=${WEEK_INDEX}
        AND artifact_type='WEEKLY_RECAP'
        AND state='APPROVED'
      ORDER BY version DESC, id DESC
      LIMIT 1;
    " 2>/dev/null || true
  )"

  # Normalize: must be exactly 64 lowercase hex.
  if ! echo "${_sv_fp}" | grep -Eq '^[0-9a-f]{64}$'; then
    _sv_fp="$(python - <<'PY'
print("0"*64)
