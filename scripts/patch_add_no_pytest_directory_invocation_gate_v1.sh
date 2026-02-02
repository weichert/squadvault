#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add gate forbidding pytest directory invocation (v1) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_add_no_pytest_directory_invocation_gate_v1.py

echo "==> bash -n"
bash -n scripts/check_no_pytest_directory_invocation.sh
bash -n scripts/prove_ci.sh

echo "==> self-test (must FAIL on directory invocation)"
tmp="${TMPDIR:-/tmp}/sv_bad_pytest_dir_$$.sh"
cleanup() { rm -f "$tmp" >/dev/null 2>&1 || true; }
trap 'cleanup' EXIT

cat > "$tmp" <<'BAD'
#!/usr/bin/env bash
pytest -q Tests/validation/signals
BAD

set +e
bash scripts/check_no_pytest_directory_invocation.sh "$tmp" >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR: self-test expected failure but gate returned success" >&2
  exit 2
fi
echo "OK: self-test failure observed (as expected)"

echo "==> self-test (must PASS on pinned list style)"
tmp2="${TMPDIR:-/tmp}/sv_good_pytest_$$.sh"
cat > "$tmp2" <<'GOOD'
#!/usr/bin/env bash
pytest -q Tests/test_example_v1.py
GOOD

bash scripts/check_no_pytest_directory_invocation.sh "$tmp2" >/dev/null
rm -f "$tmp2" >/dev/null 2>&1 || true
echo "OK: self-test pass observed (as expected)"

echo "OK"
