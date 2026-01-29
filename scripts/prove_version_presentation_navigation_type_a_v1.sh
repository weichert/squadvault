#!/usr/bin/env bash
set -euo pipefail

echo "=== Proof: Version Presentation & Navigation — Type A invariants (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> py_compile"
PYTHONPATH=src python -m py_compile src/squadvault/core/versioning/version_presentation_navigation_v1.py
echo "OK: compile"

echo
echo "==> unit test (path-import workaround)"
python Tests/test_version_presentation_navigation_v1.py -q
echo "OK: tests"
