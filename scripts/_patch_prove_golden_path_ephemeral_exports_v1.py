from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

ANCHOR_CALL = "./scripts/recap.sh export-assemblies \\"
ANCHOR_WEEKDIR = 'WEEK_DIR="artifacts/exports/${LEAGUE_ID}/${SEASON}/week_$(printf \'%02d\' "$WEEK_INDEX")"'


INSERT_BEFORE_CALL = r'''
# SV_PATCH: golden path ephemeral exports by default (v1)
# Default behavior: write export artifacts to a temp export root to keep fresh clones clean.
# Opt-in persistence: set SV_KEEP_EXPORTS=1 to use the default export root ("artifacts").
SV_KEEP_EXPORTS="${SV_KEEP_EXPORTS:-0}"
EXPORT_ROOT="artifacts"
_SV_GP_TMP_EXPORT_ROOT=""

if [[ "$SV_KEEP_EXPORTS" != "1" ]]; then
  _SV_GP_TMP_EXPORT_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/sv_golden_path_exports.XXXXXX")"
  EXPORT_ROOT="$_SV_GP_TMP_EXPORT_ROOT"
fi

# Cleanup temp export root (chain EXIT trap if one already exists)
if [[ -n "${_SV_GP_TMP_EXPORT_ROOT:-}" ]]; then
  _sv_gp_prev_exit_trap="$(trap -p EXIT | sed -E "s/^trap -- '(.*)' EXIT$/\1/")"
  if [[ -n "${_sv_gp_prev_exit_trap:-}" ]]; then
    trap "${_sv_gp_prev_exit_trap}; rm -rf '${_SV_GP_TMP_EXPORT_ROOT}'" EXIT
  else
    trap "rm -rf '${_SV_GP_TMP_EXPORT_ROOT}'" EXIT
  fi
fi
# /SV_PATCH: golden path ephemeral exports by default (v1)
'''.lstrip("\n")

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if "SV_PATCH: golden path ephemeral exports by default (v1)" in text:
        print("No changes needed.")
        return 0

    if ANCHOR_CALL not in text:
        raise SystemExit("ERROR: could not find export-assemblies invocation anchor")

    # Insert export-root logic immediately before the export-assemblies call
    text = text.replace(ANCHOR_CALL, INSERT_BEFORE_CALL + ANCHOR_CALL, 1)

    # Add --export-dir "$EXPORT_ROOT" to the export-assemblies invocation (idempotent)
    if "--export-dir" not in text:
        text = text.replace(
            "  --week-index \"$WEEK_INDEX\" || export_rc=$?\n",
            "  --week-index \"$WEEK_INDEX\" \\\n"
            "  --export-dir \"$EXPORT_ROOT\" || export_rc=$?\n",
            1,
        )

    # Update WEEK_DIR to use EXPORT_ROOT
    if ANCHOR_WEEKDIR not in text:
        # Allow for minor drift by matching the artifacts/exports prefix
        needle = 'WEEK_DIR="artifacts/exports/${LEAGUE_ID}/${SEASON}/week_$(printf'
        if needle not in text:
            raise SystemExit("ERROR: could not find WEEK_DIR anchor for exports path")
        # Replace only the leading root portion
        text = text.replace('WEEK_DIR="artifacts/exports/', 'WEEK_DIR="${EXPORT_ROOT}/exports/', 1)
    else:
        text = text.replace(
            ANCHOR_WEEKDIR,
            'WEEK_DIR="${EXPORT_ROOT}/exports/${LEAGUE_ID}/${SEASON}/week_$(printf \'%02d\' "$WEEK_INDEX")"',
            1,
        )

    TARGET.write_text(text, encoding="utf-8")
    print(f"Patched: {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
