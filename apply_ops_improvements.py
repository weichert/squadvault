#!/usr/bin/env python3
"""Apply: three targeted ops improvements.

1. Fix scripts/py to export PYTHONPATH — eliminates manual PYTHONPATH=src prefix
2. Fix scripts/reprocess_full_season.py artifact_id=? → version number
3. Strengthen golden path EAL assertion — verify directive value, not just non-None
"""

import pathlib

ROOT = pathlib.Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────
# 1. Fix scripts/py to set PYTHONPATH
# ─────────────────────────────────────────────────────────────────────

py_shim = ROOT / "scripts" / "py"
py_shim.write_text('''\
#!/usr/bin/env bash
set -euo pipefail

# scripts/py — canonical python shim (v2)
# Goals:
# - CWD-independent (safe under any working directory)
# - Deterministic tool selection (prefer python3, fallback to python)
# - Exec passthrough (propagate exit code)
# - Sets PYTHONPATH so callers never need to
repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"
export PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$@"
fi

echo "ERROR: python3/python not found on PATH" >&2
exit 127
''')
py_shim.chmod(0o755)
print(f"✓ Wrote {py_shim.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 2. Fix batch reprocessor output (artifact_id=? → version)
# ─────────────────────────────────────────────────────────────────────

batch_path = ROOT / "scripts" / "reprocess_full_season.py"
old_text = batch_path.read_text()

old_line = '                print(f"           regen OK: artifact_id={getattr(res, \'artifact_id\', \'?\')}")'
new_line = '                print(f"           regen OK: version={res.version} new={res.created_new}")'

assert old_line in old_text, f"Could not find expected line in reprocess_full_season.py"
new_text = old_text.replace(old_line, new_line)
batch_path.write_text(new_text)
print(f"✓ Patched {batch_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 3. Strengthen golden path EAL assertion
# ─────────────────────────────────────────────────────────────────────

gp_path = ROOT / "Tests" / "test_golden_path_lock_v1.py"
gp_text = gp_path.read_text()

# Add the import for EAL constants
old_import_block = "from squadvault.recaps.weekly_recap_lifecycle import ("
new_import_block = """\
from squadvault.core.eal.editorial_attunement_v1 import (
    EAL_MODERATE_CONFIDENCE_ONLY,
)
from squadvault.recaps.weekly_recap_lifecycle import ("""

assert old_import_block in gp_text, "Could not find lifecycle import in golden path test"
gp_text = gp_text.replace(old_import_block, new_import_block, 1)

# Strengthen the assertion
old_assertion = """\
        assert eal_row is not None and eal_row[0] is not None, (
            "Step 8: EAL directive persisted as audit metadata"
        )"""

new_assertion = """\
        assert eal_row is not None and eal_row[0] is not None, (
            "Step 8: EAL directive persisted as audit metadata"
        )
        assert eal_row[0] == EAL_MODERATE_CONFIDENCE_ONLY, (
            f"Step 8: EAL directive should be MODERATE_CONFIDENCE_ONLY for "
            f">=3 events, got {eal_row[0]!r}"
        )"""

assert old_assertion in gp_text, "Could not find EAL assertion in golden path test"
gp_text = gp_text.replace(old_assertion, new_assertion, 1)

gp_path.write_text(gp_text)
print(f"✓ Patched {gp_path.relative_to(ROOT)}")


print()
print("Apply complete. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
print()
print("Then test the shim fix:")
print("  ./scripts/py scripts/reprocess_full_season.py --db .local_squadvault.sqlite \\")
print("      --league-id 70985 --season 2024 --start-week 1 --end-week 1")
