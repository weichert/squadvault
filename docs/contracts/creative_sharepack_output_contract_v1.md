# Creative Sharepack Output Contract (v1)

**Contract ID:** CREATIVE_SHAREPACK_OUTPUT_CONTRACT_V1  
**Status:** Draft (v1)  
**Scope:** `artifacts/creative/**/sharepack_v1/*` and sharepack-related export assemblies

## Purpose

Define the **stable, auditable outputs** produced by the Creative Sharepack pipeline so:
- CI can verify determinism and structural invariants
- Downstream creative surfaces can safely depend on filenames + minimal structure
- Future versions can evolve without breaking v1 consumers

## Output Roots

- `artifacts/creative/<league_id>/<season>/week_<WW>/sharepack_v1/`
- (Optional exports) `artifacts/exports/<league_id>/<season>/week_<WW>/assembly_sharepack_v1__approved_v01.md`

## Required Files

Within:

`artifacts/creative/<league>/<season>/week_<WW>/sharepack_v1/`

Required (v1):
- `README.md`
- `manifest_v1.json`
- `commentary_short_v1.md`
- `memes_caption_set_v1.md`
- `stats_fun_facts_v1.md`

Notes:
- Additional files may appear, but v1 consumers MUST NOT require them unless this contract is updated.
- Filenames are part of the contract for v1.

## Minimal Structural Invariants

- All required files must exist when sharepack generation is invoked for a given league/week.
- `manifest_v1.json` must be valid JSON.
- Any directory enumeration used to build sharepacks MUST be explicitly ordered (sorted) to ensure determinism.

## Versioning Rules

- Breaking changes (renames, moves, required file removals) require a new contract version.
- Non-breaking additions are allowed if existing required files remain unchanged in name/location.

## Enforced By

(If/when wired)
- A gate script should validate presence + basic invariants for required files.
- CI proof(s) may conditionally run based on fixture availability.

