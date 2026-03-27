# scripts/ — Operational Tooling

Only active operational scripts live at this root.
Historical development artifacts (applied patches, one-time migration scripts) are in `_archive/`.

## Categories

- `recap.sh` — Operator entrypoint for the recap CLI
- `py` — Deterministic Python entrypoint shim (sets PYTHONPATH)
- `prove_*.sh` — Proof scripts (golden path, end-to-end verification)
- `gate_*.sh` — Gate scripts (CWD independence, shim compliance)
- `check_*.sh` — Check scripts (schema drift, structural invariants)
- `gen_*.py` — Generation scripts (season HTML export, etc.)
- `run_*.sh` — Runner scripts (test suite, pipeline steps)

## Archived

- `_archive/` — Historical development artifacts (tracked in git, not active)
- `_archive/applied/` — One-time apply/patch scripts that have been run
- `_archive/patches/` — Incremental patch scripts from development history
- `_graveyard/` — Permanently retired scripts
- `_retired/` — Retired but potentially reusable scripts
