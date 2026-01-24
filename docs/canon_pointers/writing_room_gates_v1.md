# Canonical Boundary Pointers — Writing Room Gates v1

Writing Room v1 behavior is governed by deterministic gates and tests.

## Gates

- Writing Room gate:
  - `scripts/run_writing_room_gate_v1.sh`

- Shim compliance:
  - `scripts/check_shims_compliance.sh`

- CWD independence:
  - `scripts/gate_cwd_independence_shims_v1.sh`

## Canonical invariants (v1)

- Output is a bounded side-artifact:
  - `artifacts/writing_room/<league>/<season>/week_<NN>/selection_set_v1.json`

- Output is deterministic for a given DB + week window + rules.
- Exclusions are explicit (e.g., `INTENTIONAL_SILENCE`).
- Withhold behavior is enforced when only intentionally-silent signals exist.

## In-repo source of truth

- Consumer:
  - `src/squadvault/consumers/recap_writing_room_select_v1.py`

- Schema:
  - `src/squadvault/recaps/writing_room/selection_set_schema_v1.py`

- Tests:
  - `Tests/test_writing_room_*`
