# PFL Buddies Recap Archive

This directory is the append-only archive of approved weekly recaps that
have been distributed to the league.

Each distribution produces two files in `<season>/`:

- `week_<NN>__v<V>.md` — the league-facing message, with YAML frontmatter
  carrying identity, provenance, approval, and distribution metadata.
- `week_<NN>__v<V>.json` — internal-audience companion (audit, debugging,
  verifier re-run). Mirrors the frontmatter and includes the full
  `rendered_text` for fact reconstruction.

## Invariants

- **Append-only.** Distributed artifacts are never silently revised. If
  `recap_artifacts` produces a new `version` for the same `(season,
  week_index)` and it is later distributed, that is a separate archive
  file with a higher `__vN` suffix.
- **APPROVED-only.** Files in this directory correspond to engine
  artifacts in state `APPROVED` at the time of distribution. The Recap
  Review Heuristic governs approval; this archive records what
  approval-then-distribution produced, not what was drafted.
- **Distribution events live here.** The archive frontmatter is the
  canonical record of when and where a recap was distributed. The
  engine database does not record distribution events.

## Adding to this archive

Distribution is governed by `docs/runbooks/distribution_v1.md`. Do not
write files into this directory by hand; the runbook's single command
produces them deterministically.

## Layout test

`Tests/test_archive_layout_v1.py` enforces the structural invariants
above (filename pattern, paired companion, required frontmatter keys,
season-directory consistency). The test is vacuous when the archive is
empty and tightens automatically as it fills.
