# SquadVault — Writing Room (Build Phase)

This package implements the Writing Room layer as **contract-driven, deterministic, testable code**.

## Scope (Sprint 1)
Sprint 1 creates **module skeletons and schema types only**.

- ✅ Package scaffolding
- ✅ Intake stub (no logic)
- ✅ Selection Set Schema stub (no types yet)

## Non-Scope (Explicit)
- No scoring, ranking, or heuristics
- No freeform narrative generation
- No new data sources
- No “helpful” inferred fields

## Determinism Rules (Do Not Invent)
- Inputs are treated as **opaque**; we do not define a Signal schema here.
- Any required fields must be read via an explicit adapter/extractor (introduced in later tasks).
- Ordering and fingerprinting must be stable and contract-defined.

## Files
- `intake_v1.py` — Writing Room intake entrypoint (stub)
- `selection_set_schema_v1.py` — Selection Set Schema (types to be added in T2)
