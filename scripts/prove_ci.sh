#!/usr/bin/env bash
set -euo pipefail

echo "== CI Proof Suite =="

bash scripts/check_shell_syntax.sh
bash scripts/check_shims_compliance.sh
bash scripts/check_no_memory_reads.sh

bash scripts/prove_eal_calibration_type_a_v1.sh
bash scripts/prove_tone_engine_type_a_v1.sh
bash scripts/prove_version_presentation_navigation_type_a_v1.sh

# Golden path uses local db by default; point it at the fixture explicitly if supported.
# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.
if bash scripts/prove_golden_path.sh --help 2>/dev/null | grep -q -- '--db'; then
  bash scripts/prove_golden_path.sh --db fixtures/ci_squadvault.sqlite --league-id 70985 --season 2024 --week-index 6
else
  bash scripts/prove_golden_path.sh
fi

echo
echo "=== CI: Rivalry Chronicle end-to-end (fixture) ==="
SV_PROVE_TS_UTC="2026-01-01T00:00:00Z" ./scripts/prove_rivalry_chronicle_end_to_end_v1.sh \
  --db fixtures/ci_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --approved-by "ci"

echo "OK: CI proof suite passed"
