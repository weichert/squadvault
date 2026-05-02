# Reception Capture Runbook v1

## Purpose & scope

This runbook covers recording reception observations against archived
distributions: replies, reactions, unprompted references, and the
close of the 7-day silence window if no observations occurred.

Reception observations exist to inform voice quality (does the
content feel like the league?), not engagement (does the league
engage more?). The Platform Guardrails forbid optimizing for
engagement metrics; this runbook and the underlying tooling honor
that constraint. **Captured observations are facts. They are not
counted, scored, ranked, or aggregated into engagement signal.**

Scope:

- One observation per invocation. Multiple observations against the
  same distribution are recorded by running the script multiple
  times.
- The runbook covers the `group_text_paste_assist` distribution
  channel (Track A's first channel). Other channels can be added
  here when their distribution flow lands.

Out of scope:

- Voice iteration. Track C is where reception data influences
  composition, when there's enough of it to draw conclusions from.
- Edit-diff capture (different surface; deferred).
- Member registry / consent tracking. Track E.

## When to record

Record an observation **as soon as it is observed**, not in batches.
The closer the timestamp is to the moment of the observation, the
more useful the record is for any future voice retrospective.

What counts as a reception observation:

- A **reply** in the thread responding to the recap.
- A **reaction** (emoji, tap-back) on the recap message.
- An **unprompted reference** — in the thread later, in person, in
  another channel — that mentions or alludes to the recap.

What does not:

- Hypothetical reactions you imagine someone might have.
- Sentiment you infer without direct evidence.
- General league chatter that does not reference the distributed
  content.
- Your own internal reactions to the recap. Those go in observation
  memos, not the reception log.

## The four kinds

The `--kind` flag is a closed enum. Adding a new kind is a runbook
revision, not a per-use decision.

- `reply` — a text response in the thread. Required: `--content`
  (the gist of the reply, paraphrased or quoted; keep it brief).
- `reaction` — a tap-back, emoji, or non-text acknowledgment.
  Recommended: `--content "thumbs_up"` (or whatever the platform
  reports). The reaction's name is the content.
- `reference` — an unprompted mention in another context (later in
  the thread, in person, in another channel). Required: `--content`
  describing what was referenced. Use `--context` to record where
  the reference happened.
- `silence_period_close` — the 7-day reception window has closed.
  Allowed at most once per artifact, must be the last observation
  recorded. Use `--silence-window-close` shorthand. Member and
  content are null. The script generates a default note based on
  prior observations.

## The single command

```
./scripts/py scripts/record_reception.py \
    --season 2025 --week-index 7 --version 27 \
    --kind reply --member miller \
    --content "haha brutal on the bench points line"
```

For multi-line / pasted content:

```
./scripts/py scripts/record_reception.py \
    --season 2025 --week-index 7 --version 27 \
    --kind reference --member stu --content-stdin
[paste, then Ctrl-D]
```

For window close (after 7 days with nothing further to record):

```
./scripts/py scripts/record_reception.py \
    --season 2025 --week-index 7 --version 27 \
    --silence-window-close
```

Optional flags on every form:

- `--member <name>` — franchise short or owner first name.
  Free-form. There is no member registry today.
- `--observed-by <name>` — defaults to current OS user. Override
  if recording on someone else's behalf.
- `--observed-at <iso>` — defaults to now. Override if recording
  after the fact.
- `--context <label>` — defaults to `group_text_thread`. Use
  something like `in_person` or `text_followup` for references.
- `--notes <text>` — optional commissioner note.
- `--archive-root <path>` — defaults to `archive/recaps`.
- `--yes` — skip the confirmation prompt.

## What you'll see

1. The script reads the archive `.md` for the requested
   `(season, week_index, version)`. If missing, exits 2.
2. It computes the next `observation_id` by scanning the existing
   sibling reception file (or starts at 1 if none).
3. It refuses to add a second `silence_period_close` (exit 4).
4. It shows you the observation it's about to write and prompts
   for confirmation.
5. On confirm, it appends one YAML document to:
   ```
   archive/recaps/<season>/week_<NN>__v<V>__reception.yaml
   ```
6. For `silence_period_close`, it prints a suggested observation
   memo path and skeleton. Filing the memo is a commissioner
   reflection task, not automated.

## After recording

Each observation creates an unstaged change. Commit when convenient
— observations don't need to be committed individually; batching is
fine if multiple come in close together.

Suggested commit message:
```
archive: reception observation s<S> w<W> v<V> (id<N>, <kind>)
```

For window close:
```
archive: reception window close s<S> w<W> v<V>
```

## Verifying exit criterion #4

Track A's exit criterion #4 (a real PFL Buddies member has read the
recap) is closed by:

- **Any** recorded reception observation of kind `reply`,
  `reaction`, or `reference` in the 7-day window after distribution.
  That is direct evidence of reception and the criterion is met.
- A `silence_period_close` recorded after 7 days with no other
  observations is **not** closure of #4 — it is a finding (the
  league did not externally signal reception of this piece). File
  the suggested observation memo when this happens. Silence around
  a Writer's Room piece is information about the league's
  relationship to the output, not a failure.

## Failure modes

### No archive entry found

Exit code 2. The script's stderr names the path it looked for. If
the season/week/version is right, the distribution may not have
happened yet — distribute first via
`scripts/distribute_recap.py`.

### `silence_period_close` already recorded

Exit code 4. The terminal kind is unique per artifact. If
additional observations come in after the window has closed, that
is itself a finding worth a memo, but the reception log has
finalized.

### Invalid argument combination

Exit code 3. The most common cases:

- `--kind reply` or `--kind reference` without `--content`.
- `--content` and `--content-stdin` both supplied.
- `--silence-window-close` combined with `--kind <other>`.

### Commissioner aborts before confirmation

Exit code 5. No file is touched.

## What this runbook does not include

- **Engagement metrics or analytics** — forbidden by the Platform
  Guardrails.
- **Aggregations across observations** — counts, rates, "members
  who responded most," reaction-frequency anything. Not produced;
  not buildable from this surface.
- **Inferences about why a member did or didn't respond.** Those
  are voice-iteration speculation, not reception facts. They
  belong in observation memos under Track C reflection.
- **Editing recorded observations.** The reception log is
  append-only at the file level. If an observation was recorded
  incorrectly, write a new observation that contextualizes the
  earlier one (e.g., a `reference` whose `notes` say "This
  contextualizes id 3 — the speaker was Stu, not Steve.").

## Cross-references

- `docs/runbooks/distribution_v1.md` — the distribution flow that
  produces archive entries to attach reception to.
- `archive/recaps/README.md` — the archive layout including the
  sibling reception file pattern.
- `Platform_and_Writers_Room_Compact_v1_0.md` — vision-level
  source of the "no engagement loops" guardrail.
- `SquadVault_Operational_Plan_v1_1.md` — Track B definition.
- `Tests/test_reception_capture_v1.py` — structural enforcement.
