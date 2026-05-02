# PFL Buddies Recap Archive

This directory is the append-only archive of approved weekly recaps that
have been distributed to the league.

Each distribution produces two files in `<season>/`:

- `week_<NN>__v<V>.md` — the league-facing message, with YAML frontmatter
  carrying identity, provenance, approval, and distribution metadata.
- `week_<NN>__v<V>.json` — internal-audience companion (audit, debugging,
  verifier re-run). Mirrors the frontmatter and includes the full
  `rendered_text` for fact reconstruction.

When reception observations are recorded, an additional sibling file
accumulates alongside:

- `week_<NN>__v<V>__reception.yaml` — append-only stream of observed
  reception events (replies, reactions, unprompted references, or the
  close of the silence window). Created lazily on first observation;
  absent until something is recorded. The original `.md` and `.json`
  are never touched after creation.

## Invariants

- **Append-only.** Distributed artifacts are never silently revised. If
  `recap_artifacts` produces a new `version` for the same `(season,
  week_index)` and it is later distributed, that is a separate archive
  file with a higher `__vN` suffix. Reception observations append to
  the sibling YAML file as new documents; prior documents are never
  rewritten.
- **APPROVED-only.** Files in this directory correspond to engine
  artifacts in state `APPROVED` at the time of distribution. The Recap
  Review Heuristic governs approval; this archive records what
  approval-then-distribution produced, not what was drafted.
- **Distribution events live here.** The archive frontmatter is the
  canonical record of when and where a recap was distributed. The
  engine database does not record distribution events.
- **Reception observations live here too, separately.** Reception
  observations are facts about how the league related to a piece. They
  are not metrics, not aggregable, and not produced by the engine — a
  commissioner records them via the reception capture runbook.

## Adding to this archive

Distribution is governed by `docs/runbooks/distribution_v1.md`.
Reception observations are governed by
`docs/runbooks/reception_capture_v1.md`. Do not write files into this
directory by hand; the runbooks' single commands produce them
deterministically.

## Layout tests

`Tests/test_archive_layout_v1.py` enforces the structural invariants of
the distribution `.md`/`.json` pair (filename pattern, paired
companion, required frontmatter keys, season-directory consistency).

`Tests/test_reception_capture_v1.py` enforces the structural invariants
of the reception sibling file (filename pattern, pairing with the
archive `.md`, document stream parseability, required keys, monotonic
`observation_id`, closed `kind` enum, `silence_period_close` is
terminal and unique).

Both tests are vacuous when the archive is empty and tighten
automatically as it fills.

