# Canonical Boundary Pointers — Selection Set Boundary v1

The Writing Room consumes **only** the Selection Set side-artifact (v1).
No other raw event payloads or non-deterministic data are permitted inputs to Writing Room narrative logic.

## Artifact boundary

- `artifacts/writing_room/<league>/<season>/week_<NN>/selection_set_v1.json`

## Schema + governance

- Schema module (source of truth):
  - `src/squadvault/recaps/writing_room/selection_set_schema_v1.py`

- Governance tests:
  - `Tests/test_writing_room_selection_set_schema_v1.py`
  - `Tests/test_writing_room_selection_set_v1.py`

## Enforcement

- Gate:
  - `scripts/run_writing_room_gate_v1.sh`
