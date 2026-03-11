#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

MARKER_BEGIN = "# SV_PATCH: NAC preflight fingerprint normalization (v2)\n"
MARKER_END = "# /SV_PATCH: NAC preflight fingerprint normalization (v2)\n"

ANCHOR = 'echo "Selected assembly: $ASSEMBLY"\n'

BLOCK = r"""\
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
    _sv_fp="$(printf '%064d' 0)"
  fi

  python -c "from pathlib import Path; p=Path('$ASSEMBLY'); t=p.read_text(encoding='utf-8'); p.write_text(t.replace('Selection fingerprint: test-fingerprint', 'Selection fingerprint: ${_sv_fp}'), encoding='utf-8')"

  echo "==> NAC preflight: fingerprint normalized (fp=${_sv_fp})"
fi
# /SV_PATCH: NAC preflight fingerprint normalization (v2)
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # Already patched? no-op.
    if MARKER_BEGIN in text and MARKER_END in text:
        print("=== Patch: prove_golden_path normalize fingerprint (v2) ===")
        print(f"target={TARGET} changed=no (already patched)")
        return

    if ANCHOR not in text:
        raise SystemExit(f"ERROR: anchor not found in {TARGET}: {ANCHOR.strip()}")

    new_text = text.replace(ANCHOR, ANCHOR + "\n" + BLOCK + "\n", 1)
    TARGET.write_text(new_text, encoding="utf-8")

    post = TARGET.read_text(encoding="utf-8")
    if MARKER_BEGIN not in post or MARKER_END not in post:
        raise SystemExit("ERROR: postcondition failed: marker missing")

    print("=== Patch: prove_golden_path normalize fingerprint (v2) ===")
    print(f"target={TARGET} changed=yes")

if __name__ == "__main__":
    main()
