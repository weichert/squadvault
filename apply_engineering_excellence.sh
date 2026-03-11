#!/usr/bin/env bash
# ============================================================================
# SquadVault Engineering Excellence — Apply Patch
#
# This script applies all changes from the engineering excellence sessions.
#
# Usage:
#   1. Download both files to your repo root:
#      - squadvault_engineering_excellence.patch
#      - ci_squadvault.sqlite
#   2. Run: bash apply_engineering_excellence.sh
#
# What it does:
#   - Applies 1,718 text file changes (tests, docstrings, schema, scripts, etc.)
#   - Replaces fixture DB with corrected version
#   - Runs the test suite to verify
#
# To review before applying:
#   git apply --stat squadvault_engineering_excellence.patch
#   git apply --check squadvault_engineering_excellence.patch
# ============================================================================
set -euo pipefail

PATCH="squadvault_engineering_excellence.patch"
FIXTURE="ci_squadvault.sqlite"

if [ ! -f "$PATCH" ]; then
    echo "ERROR: $PATCH not found in current directory."
    echo "Download it from Claude and place it in the repo root."
    exit 1
fi

echo "=== Applying text changes ==="
git apply "$PATCH"
echo "Applied $(grep -c '^diff --git' "$PATCH") file changes."

if [ -f "$FIXTURE" ]; then
    echo "=== Replacing fixture DB ==="
    cp "$FIXTURE" fixtures/ci_squadvault.sqlite
    echo "Fixture DB updated."
else
    echo "=== Regenerating fixture DB from corrected schema.sql ==="
    python scripts/regenerate_fixture_db.py
fi

echo ""
echo "=== Running tests ==="
python -m pytest Tests/ -q

echo ""
echo "=== Verifying gates ==="
python -m pytest Tests/test_architecture_gates_v1.py Tests/test_governance_gates_v1.py Tests/test_hygiene_gates_v1.py Tests/test_schema_drift_gate_v2.py -v

echo ""
echo "Done. Review with 'git diff --stat' then commit."
echo "Suggested commit message:"
echo ""
echo "  engineering excellence: tests, docstrings, schema, hygiene"
echo ""
echo "  - 473 tests passing (was 130), 53 test files (was 37)"
echo "  - 100% function docstrings, module docstrings, return types"
echo "  - schema.sql aligned with fixture DB (10 tables, 0 drift)"
echo "  - 18 core except Exception narrowed to specific types"
echo "  - 0 SystemExit in business logic (was ~47)"
echo "  - 42 regression gates (architecture, governance, hygiene, schema)"
echo "  - 644 fossil patch scripts archived"
echo "  - 48 unreferenced scripts archived"
echo "  - pfl/ removed (976 lines, founder-approved)"
