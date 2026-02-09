# Golden Path Output Contract (v1)

## Enforced By

- `scripts/prove_golden_path.sh`
- `scripts/gate_golden_path_output_contract_v1.sh`

Status: CANONICAL (contract)
Applies To: Golden Path export assemblies produced by `scripts/run_golden_path_v1.sh`
Version: v1

## Purpose

This contract locks down the **filesystem shape** of Golden Path creative output so downstream creative tooling
(memes, video, remixers, etc.) can rely on stable paths and naming without guesswork.

This contract enforces **structure only** (paths, naming, and minimal markdown structure). It does **not**
evaluate narrative quality, tone, humor, or factual content.

## Contracted Output Unit

The canonical handle for Golden Path output is the **Selected Assembly** file path:

- Emitted in logs as: `Selected assembly: <absolute_path>`
- Must resolve to a markdown file under the export tree:
  `.../exports/<league_id>/<season>/week_<NN>/<assembly_filename>.md`

The contract validates:
- The selected assembly path exists
- Its location matches the required export directory shape
- Required sibling assembly exists (plain ↔ sharepack pairing)
- Naming invariants hold
- Minimal markdown structural expectations are met (not content)

## Required Directory Shape

Selected assembly MUST be located at:

`exports/<league_id>/<season>/week_<NN>/...`

Where:
- `<league_id>` is digits
- `<season>` is 4 digits (e.g., 2024)
- `week_<NN>` is zero-padded two digits (e.g., week_06)

## Required Files Per Week Directory

Within the week directory containing the selected assembly:

- `assembly_plain_v1__approved_vNN.md` MUST exist
- `assembly_sharepack_v1__approved_vNN.md` MUST exist

The selected assembly MUST be one of the above.

`vNN` is a zero-padded two-digit version (e.g., v01, v02).

## Naming Invariants

Assembly filename MUST match one of:

- `assembly_plain_v1__approved_vNN.md`
- `assembly_sharepack_v1__approved_vNN.md`

No other filename patterns are contracted in v1.

## Minimal Markdown Structure (structure-only)

Each required assembly file MUST:
- Be non-empty
- Contain at least one Markdown heading line beginning with `#` within the first 80 lines

This is intentionally minimal and does not enforce any specific wording.

## Explicit Non-Enforcement (Important)

This contract does NOT enforce:
- Any narrative wording, tone, humor, or quality
- Counts of facts, bullets, sections, jokes, etc.
- Any ranking/scoring/analytics/optimization logic
- Any deterministic *content* beyond the already-proven determinism of Golden Path
- Persistence of temp export roots unless the operator explicitly opts in (e.g. SV_KEEP_EXPORT_TMP)

## Versioning Rules

- Breaking changes require a new contract version file (v2, v3…).
- Gates must pin to a specific contract version.
- Silent drift is forbidden.
