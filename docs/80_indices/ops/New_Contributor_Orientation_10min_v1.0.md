# New Contributor Orientation (10 min) (v1.0)

Purpose:
Get productive quickly without violating SquadVault’s process discipline.

This is an index only. Authority remains in the linked canonical documents.

## Read in this order (10 minutes)

1. [How to Read SquadVault](<../../canon_pointers/How_to_Read_SquadVault_v1.0.md>)
2. [Rules of Engagement](<../../process/rules_of_engagement.md>)
3. [Canonical Patcher/Wrapper Pattern](<../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md>)
4. [Canonical Indices Map](<Canonical_Indices_Map_v1.0.md>)
5. [Ops Rules — One Page](<Ops_Rules_One_Page_v1.0.md>)

## Do on day 1 (copy/paste)

- Prove CI from a clean repo:
  - `bash scripts/prove_ci.sh`
- Run the canonical noop patch (verifies patch workflow plumbing):
  - `bash scripts/patch_example_noop_v1.sh`
- Confirm cleanliness:
  - `git status --porcelain=v1`

## If something fails

- Use safe recovery steps: [Recovery Workflows Index](<Recovery_Workflows_Index_v1.0.md>)
- Start from guardrails: [CI Guardrails Index](<CI_Guardrails_Index_v1.0.md>)
