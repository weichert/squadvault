#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: weekly recap clean-room safety (materialize ACTIVE recap json) (v1) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_weekly_recap_materialize_active_recap_json_v1.py

echo "==> py_compile"
PYTHONPATH=src "$python" -m py_compile src/squadvault/recaps/weekly_recap_lifecycle.py

echo "==> bash -n (ci runner)"
bash -n scripts/prove_ci.sh

echo "==> focused regression (EAL writer boundary; fixture-safe db copy)"
SV_TMPDIR="${TMPDIR:-/tmp}"
SV_TMPDIR="${SV_TMPDIR%/}"
WORK_DB="$(mktemp "${SV_TMPDIR}/squadvault_local_workdb.XXXXXX")"
cleanup_work_db() { rm -f "${WORK_DB}" >/dev/null 2>&1 || true; }
trap 'cleanup_work_db' EXIT
cp -p "fixtures/ci_squadvault.sqlite" "${WORK_DB}"
export SQUADVAULT_TEST_DB="${WORK_DB}"

rm -f artifacts/recaps/70985/2024/week_06/recap_v01.json || true
SV_DEBUG=1 PYTHONPATH=src \
  pytest -q Tests/test_eal_writer_boundary_v1.py::TestEALWriterBoundaryV1::test_eal_writer_does_not_affect_selection_or_facts

echo "OK"
