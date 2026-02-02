# Canonical Boundary Pointers — Writing Room Export Contract v1

The Writing Room produces shareable/exportable artifacts derived **only** from the Selection Set boundary (v1).

This repo does not vendor the canonical narrative/export contract docs; they live as project-file artifacts / data-room exports.
This file records the repo-side boundaries and enforcement surfaces for export.

## Inputs (allowed)

- Selection Set v1 (only):
  - `artifacts/writing_room/<league>/<season>/week_<NN>/selection_set_v1.json`

## Outputs (expected)

- Export artifact(s) produced from Selection Set v1, suitable for editorial or downstream consumers.
- No raw canonical event payloads or non-deterministic inputs are permitted in export generation.

## Enforcement

- Boundary pointer:
  - `docs/canon_pointers/selection_set_boundary_v1.md`

- Gates:
  - `docs/canon_pointers/writing_room_gates_v1.md`
  - `scripts/run_writing_room_gate_v1.sh`

## In-repo implementation anchors

- Selection producer:
  - `src/squadvault/consumers/recap_writing_room_select_v1.py`

- Schema:
  - `src/squadvault/recaps/writing_room/selection_set_schema_v1.py`
