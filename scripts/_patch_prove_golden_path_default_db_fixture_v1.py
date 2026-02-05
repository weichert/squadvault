from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

ANCHOR = 'DB="${WORK_DB:-${CI_WORK_DB:-${DB:-.local_squadvault.sqlite}}}"  # prove_golden_path_use_work_db_v2'

INSERT = r'''
# SV_PATCH: golden path default DB uses fixture temp copy (v1)
# If no DB is provided (falls back to .local_squadvault.sqlite) and the schema isn't present,
# use an immutable fixture copied to a temp DB. This keeps Golden Path self-contained on fresh clones.
_SV_GP_TMP_DB=""
_sv_gp_db_has_recap_runs() {
  sqlite3 -noheader -batch "$1" "SELECT 1 FROM sqlite_master WHERE type='table' AND name='recap_runs' LIMIT 1;" 2>/dev/null | grep -q '^1$'
}

if [[ "${DB}" == ".local_squadvault.sqlite" ]]; then
  if [[ ! -f "${DB}" ]] || ! _sv_gp_db_has_recap_runs "${DB}"; then
    _sv_gp_fixture_db="${REPO_ROOT:-.}/fixtures/ci_squadvault.sqlite"
    if [[ ! -f "${_sv_gp_fixture_db}" ]]; then
      echo "ERROR: Golden Path default DB fixture missing: ${_sv_gp_fixture_db}" >&2
      exit 2
    fi

    _SV_GP_TMP_DB="$(mktemp "${TMPDIR:-/tmp}/sv_golden_path_db.XXXXXX")"
    cp "${_sv_gp_fixture_db}" "${_SV_GP_TMP_DB}"
    DB="${_SV_GP_TMP_DB}"
  fi
fi

# Ensure pytest uses the same DB
export SQUADVAULT_TEST_DB="${DB}"

# Clean up temp DB if we created one (avoid clobbering an existing EXIT trap)
if ! trap -p EXIT | grep -q .; then
  trap 'if [[ -n "${_SV_GP_TMP_DB:-}" && -f "${_SV_GP_TMP_DB:-}" ]]; then rm -f "${_SV_GP_TMP_DB}"; fi' EXIT
fi
# /SV_PATCH: golden path default DB uses fixture temp copy (v1)
'''

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if "SV_PATCH: golden path default DB uses fixture temp copy (v1)" in text:
        print("No changes needed.")
        return 0

    if ANCHOR not in text:
        raise SystemExit("ERROR: anchor not found for DB assignment (prove_golden_path_use_work_db_v2)")

    updated = text.replace(ANCHOR, ANCHOR + "\n" + INSERT.lstrip("\n"), 1)
    TARGET.write_text(updated, encoding="utf-8")
    print(f"Patched: {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
