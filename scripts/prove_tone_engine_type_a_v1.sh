#!/usr/bin/env bash
set -euo pipefail

echo "=== Proof: Tone Engine — Type A invariants (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> py_compile"
./scripts/py -m py_compile src/squadvault/core/tone/tone_engine_v1.py
echo "OK: compile"

echo
echo "==> unit test (path-import workaround)"
python Tests/test_tone_engine_v1.py -q
echo "OK: tests"
