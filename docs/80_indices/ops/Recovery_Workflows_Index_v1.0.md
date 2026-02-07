# Recovery Workflows Index (v1.0)

Purpose:
A 2am index of *safe* recovery workflows when CI, cleanliness, or patch discipline blocks you.

This is an index only. Authority remains in the linked canonical documents.

## Primary entrypoints

- [CI Guardrails Index](<CI_Guardrails_Index_v1.0.md>)
- [CI Cleanliness Invariant](<CI_Cleanliness_Invariant_v1.0.md>)

## Process authority

- [Rules of Engagement](<../../process/rules_of_engagement.md>)
- [Canonical Patcher/Wrapper Pattern](<../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md>)
- [Patcher/Wrapper Pairing Gate](<CI_Patcher_Wrapper_Pairing_Gate_v1.0.md>)

## Common recovery moves (safe, explicit)

- Inspect working tree:
  - `git status --porcelain=v1`
- Discard ALL tracked changes (worktree + index):
  - `git restore --staged --worktree -- .`
- Remove untracked files (destructive):
  - `git clean -fd`
- Re-run proof from a clean repo:
  - `bash scripts/prove_ci.sh`

Notes:
- If a patcher refuses-on-drift, do not “edit around it.” Update the patcher/wrapper to match the new canonical intent.
- Prefer patchers/wrappers over manual doc edits; keep changes versioned and reproducible.
