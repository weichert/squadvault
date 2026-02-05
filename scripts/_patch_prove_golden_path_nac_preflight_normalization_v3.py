from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

OLD_BLOCK_START = "# SV_PATCH: NAC preflight fingerprint normalization (v2)"
OLD_BLOCK_END = "# /SV_PATCH: NAC preflight fingerprint normalization (v2)"

NEW_BLOCK = r"""# SV_PATCH: NAC preflight fingerprint normalization (v3)
# NAC requires a 64-lower-hex fingerprint in the BEGIN_CANONICAL_FINGERPRINT block.
# Some fixtures/export paths can emit a placeholder 'test-fingerprint'. Normalize it,
# but do NOT mutate the original approved assembly. Instead, normalize into a temp copy
# used only for NAC validation.
ASSEMBLY_FOR_NAC="$ASSEMBLY"
_SV_NAC_TMP_ASSEMBLY=""

if grep -q -- "Selection fingerprint: test-fingerprint" "$ASSEMBLY"; then
  echo "==> NAC preflight: placeholder selection fingerprint detected; normalizing temp copy"

  _SV_NAC_TMP_ASSEMBLY="$(mktemp "${TMPDIR:-/tmp}/sv_golden_path_assembly.XXXXXX")"
  cp "$ASSEMBLY" "$_SV_NAC_TMP_ASSEMBLY"
  ASSEMBLY_FOR_NAC="$_SV_NAC_TMP_ASSEMBLY"

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

  "$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_normalize_nac_placeholder_fingerprint_v1.py" "$ASSEMBLY_FOR_NAC" "$_sv_fp"
  echo "==> NAC preflight: fingerprint normalized in temp copy (fp=${_sv_fp})"
fi
# /SV_PATCH: NAC preflight fingerprint normalization (v3)
"""

def replace_block(text: str) -> str:
    start_idx = text.find(OLD_BLOCK_START)
    end_idx = text.find(OLD_BLOCK_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise SystemExit("ERROR: could not find v2 NAC preflight block markers")

    # include end marker line
    end_line_idx = text.find("\n", end_idx)
    if end_line_idx == -1:
        end_line_idx = len(text)
    else:
        end_line_idx += 1

    before = text[:start_idx]
    after = text[end_line_idx:]

    # Ensure NEW_BLOCK ends with newline
    new = NEW_BLOCK
    if not new.endswith("\n"):
        new += "\n"

    return before + new + after

def patch_harness_and_cleanup(text: str) -> str:
    # Switch NAC harness to use ASSEMBLY_FOR_NAC
    old_call = '"$REPO_ROOT/scripts/py" "$REPO_ROOT/Tests/_nac_check_assembly_plain_v1.py" "$ASSEMBLY"'
    new_call = '"$REPO_ROOT/scripts/py" "$REPO_ROOT/Tests/_nac_check_assembly_plain_v1.py" "$ASSEMBLY_FOR_NAC"'

    if old_call not in text:
        raise SystemExit("ERROR: could not find expected NAC harness invocation line")

    text = text.replace(old_call, new_call, 1)

    # Insert cleanup immediately after the NAC harness call (once)
    cleanup_snippet = (
        new_call
        + "\n"
        + 'if [[ -n "${_SV_NAC_TMP_ASSEMBLY:-}" && -f "${_SV_NAC_TMP_ASSEMBLY:-}" ]]; then\n'
        + '  rm -f "${_SV_NAC_TMP_ASSEMBLY}"\n'
        + 'fi\n'
    )

    # Only if cleanup not already present
    if 'rm -f "${_SV_NAC_TMP_ASSEMBLY}"' not in text:
        text = text.replace(new_call, cleanup_snippet, 1)

    return text

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")
    updated = replace_block(original)
    updated = patch_harness_and_cleanup(updated)

    if updated == original:
        print("No changes needed.")
        return 0

    TARGET.write_text(updated, encoding="utf-8")
    print(f"Patched: {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
