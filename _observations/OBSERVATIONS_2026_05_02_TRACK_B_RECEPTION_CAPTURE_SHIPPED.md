# Observations — Track B reception capture shipped (2026-05-02)

## Summary

Track B — reception capture — shipped today as the second
operational deliverable on top of the Track A archive surface. The
mechanism records observed reception (replies, reactions, unprompted
references, or silence-window closures) as append-only YAML
documents in a sibling file next to each archived distribution.

**Shipping date correction.** A draft of this memo was prepared on
2026-04-28 and asserted same-day shipping. The delivery package was
generated but the apply script was never successfully run that night
(the test invocation failed at the zsh shell level due to a
`<placeholder>` literal being interpreted as input redirection, and
the session ended without a second attempt). The package files were
later moved to `~/.Trash/` during routine Downloads cleanup. On
2026-05-02, when reception observations from W7 became available
and `record_reception.py` was needed for the first time, the
discrepancy was discovered: the shell-level error indicated "no
such file or directory" for `scripts/record_reception.py`. The
files were recovered from Trash; two doc-only files
(`archive_recaps_README.md`, `distribution_v1_runbook.md`) had been
moved to a different state and were rebuilt; everything was
re-shipped today.

The W7 distribution (artifact v27, archived at
`archive/recaps/2025/week_07__v27.md`) is the first artifact
eligible for reception capture. The 7-day reception window opened
2026-04-28 and closes approximately 2026-05-05. Three reception
observations were available at memo time and are being recorded
into `archive/recaps/2025/week_07__v27__reception.yaml` as the
mechanism's first real use.

## What shipped

- **`scripts/record_reception.py`** — append-only CLI (single
  observation per invocation). Validates the archive entry exists,
  computes the next `observation_id`, refuses duplicate
  `silence_period_close`, prompts for confirmation, appends one YAML
  document to the sibling reception file. Prints a suggested
  observation memo skeleton on silence-window-close.
- **`Tests/test_reception_capture_v1.py`** — 14 tests total. Seven
  vacuous-when-empty layout tests (filename pattern, archive pairing,
  document parseability, required keys, monotonic id sequence,
  `kind` enum, `silence_period_close` is terminal-and-unique,
  ISO-8601 UTC timestamps). Seven emitter unit tests round-tripping
  the script's output through the layout parser.
- **`docs/runbooks/reception_capture_v1.md`** — commissioner runbook.
  Defines what counts as a reception observation, what does not,
  the four kinds, the single command per kind, exit-criterion-#4
  closure semantics, and the explicit "no engagement metrics"
  guardrail.
- **`archive/recaps/README.md`** — updated to document the sibling
  file pattern and the reception layout test.
- **`docs/runbooks/distribution_v1.md`** — updated to reference the
  reception capture mechanism in place of the prior "write an
  `_observations/` memo on silence" instruction.

## Architectural choice — sibling file over frontmatter accretion

Two ways to record post-distribution events on already-distributed
artifacts:

1. **Accrete into the existing distribution `.md` frontmatter** —
   add a `reception_observations:` block. Plausible per the
   append-only invariant ("existing keys never silently change") if
   read narrowly to permit adding new top-level keys. But it means
   every observation rewrites the `.md` (and the audit `.json`
   companion), and the file the league saw and the file in git
   diverge through edits.

2. **Sibling file per distribution** — new file
   `week_<NN>__v<V>__reception.yaml`, a stream of YAML documents
   separated by `---`, append-only at the file level (literal `>>`).
   Original `.md` and `.json` are never touched after creation.

Option B chosen. The file the league saw is byte-for-byte the file
in git; the sibling pattern composes with the existing
season/week/version layout; no schema change to the distribution
archive is required; the original distribution archive's tests
(`test_archive_layout_v1`) needed no modification.

## What worked

- **Reuse of the distribution script's YAML emitter conventions.**
  `_yaml_scalar` and `_render_frontmatter` from `distribute_recap.py`
  established the no-PyYAML pattern for the project's YAML surfaces;
  `record_reception.py` follows the same shape.
- **Closed `kind` enum (four values).** Small enough to reason
  about, structured enough to filter on, explicitly excludes any
  "magnitude" or "sentiment" field that would invite scoring drift.
- **Memo skeleton on silence-close.** Printing the suggested path
  and template makes the next step trivially followable without
  making the script generate the memo.
- **Round-trip emitter↔parser tests.** The seven emitter unit tests
  exercise the script's output against the same parser the layout
  tests use, catching any future drift locally rather than only
  through accumulated archive data.

## Findings

### F1 — "Shipped" claim drift (2026-04-28 to 2026-05-02)

The session memory and the priority list memo both carried Track B
as "shipped today" from 2026-04-28 onward. Reality: the delivery
package was generated and copied to `~/Downloads/`, but no commit
landed in the repository. The pre-existing Track A observation memo
also referenced "Track B shipped" in its post-MVP context. All three
were inaccurate.

This is exactly the failure mode the priority list re-grounding
memo (`PRIORITY_LIST_2026_04_28.md`) was created to prevent — and
yet it inherited the same drift. The drift was caught only when
`record_reception.py` was needed for the first time and the shell
reported the file missing.

**Lesson.** "Delivered" and "shipped" are different states.
Delivered means "files copied to ~/Downloads"; shipped means
"committed to origin/main." Future memos should distinguish the two
explicitly. A "shipped today" claim should reference the commit
hash; absence of a commit hash is a reliable signal that
"delivered" is the more accurate state.

A more mechanical guard: a session-start ritual that runs `git log
origin/main --since='1 week ago' --oneline | grep <topic>` against
any "recently shipped" item in carried memory. Five seconds of
verification, prevents this entire failure mode.

### F2 — Two doc files were moved to Trash and rebuilt

Of the seven Track B delivery files, six survived in `~/.Trash/`
and were restored to `~/Downloads/`. Two were not recovered:
`archive_recaps_README.md` and `distribution_v1_runbook.md`. Both
are doc-only updates to existing files. Rebuilding them was
straightforward (~5 minutes); the diffs are small and well-defined
in this memo's "What shipped" section above.

### F3 — Track B observation memo was preserved in Downloads

The original 2026-04-28 observation memo file survived the cleanup
(it was the only file with `OBSERVATIONS_*` in its name in
Downloads). This memo supersedes that one and corrects the dating.
The original is preserved as historical evidence of the drift but
is not committed to the repo.

## Reception observation status

Three observations from the W7 group text thread are being recorded
into `archive/recaps/2025/week_07__v27__reception.yaml` as the
mechanism's first use:

- Patrick Nocero — reply: "Where was this last season commish? 😊"
- Patrick Nocero — reply: "My Scores were the best on the ticker."
- Kent Paradis — reply: "We're looking forward to it, Wick!"
  (Wednesday 5:34 AM)

Track A's exit criterion #4 closes with the first recorded `reply`.
All three are recorded as evidence that reception happened across
two members and across multiple days of the window.

## Track B exit criteria status

Track B's exit criterion per the Operational Plan: "After 4–6
distributed pieces, the commissioner has structured observation of
what the league responded to and what fell flat."

Today's delivery establishes the mechanism, the runbook, and the
structural enforcement that make accumulating those observations
followable. The criterion itself is operational accumulation that
elapses over multiple distribution cycles. **Mechanism shipped.
Accumulation begins with the W7 reception observations recorded
today.**

## What is not in this delivery (deliberately)

- **Edit-diff capture.** Different surface, different mechanism.
  Deferred to a follow-up.
- **Reception retrospective format.** Premature without multiple
  weeks of data; Track C territory.
- **Member registry / stable identifiers.** `member:` is a free-form
  string today (franchise short or owner first name). Track E.
- **Aggregations of any kind.** Forbidden by the Compact, not
  buildable from this surface, not produced.
- **Automated 7-day-window-close trigger.** No scheduler, no cron,
  no reminder. The runbook prompts the commissioner to file the
  close manually. Track D may revisit.

## Cross-references

- `OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — Track A
  shipping memo, including the W7 distribution this Track B
  mechanism first attaches to.
- `Platform_and_Writers_Room_Compact_v1_0.md` — vision-level source
  of the "no engagement loops" guardrail.
- `SquadVault_Operational_Plan_v1_1.md` — Track B definition and
  exit criteria.
- `SquadVault_Recap_Review_Heuristic_Founder_Use_Only.docx` — the
  governing approval authority for distributed artifacts.
- `docs/runbooks/distribution_v1.md` — produces archive entries that
  reception capture attaches to.
- `docs/runbooks/reception_capture_v1.md` — the new runbook.
- `_observations/PRIORITY_LIST_2026_04_28.md` — referenced Track B
  as shipped; this memo's F1 finding corrects that.

---

## Addendum log

*Append-only, no silent revision. Reception observations against
the W7 distribution are recorded in
`archive/recaps/2025/week_07__v27__reception.yaml` as they happen,
not in this memo.*

### 2026-05-02 — Track B mechanism shipped (actual)

Mechanism, tests, runbook, and documentation updates landed.
Three W7 reception observations recorded immediately following.
