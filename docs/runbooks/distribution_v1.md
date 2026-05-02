# Distribution Runbook v1

## Purpose & scope

This runbook covers distributing one APPROVED weekly recap to the
league channel via paste-assisted handoff into PFL Buddies' existing
group text thread.

It does **not** cover:

- Reception capture — see `docs/runbooks/reception_capture_v1.md`
  for recording observations against a distributed artifact.
- Scheduling or cadence (Track D — future).
- Multi-channel distribution.

Distribution presupposes the artifact has already been approved per the
Recap Review Heuristic. Approval is the binding judgment about whether
a recap is fit to publish; this runbook records what was distributed,
not what was approvable.

## Preconditions

1. The target week has an APPROVED `WEEKLY_RECAP` artifact in
   `recap_artifacts`. Confirm with:
   ```
   ./scripts/py scripts/recap.py status \
       --db data/squadvault.db \
       --league-id 70985 --season <S> --week-index <W>
   ```
2. The working tree is clean. The archive write produces a single small
   commit; isolating it makes review and rollback easier.
3. The PFL Buddies group text thread is open and you can paste into it.

## The single command

```
./scripts/py scripts/distribute_recap.py \
    --db data/squadvault.db \
    --season 2025 \
    --week-index 7
```

Optional flags:

- `--league-id <id>` — defaults to `70985`.
- `--archive-root <path>` — defaults to `archive/recaps`.
- `--distributed-to <label>` — defaults to `league_channel`.
- `--channel <name>` — currently only `group_text_paste_assist`.
- `--dry-run` — produces the scratchpad but does not prompt or archive.
- `--confirm-pasted` — non-interactive; assumes the paste already
  happened. See the failure-mode notes before using.

## What you'll see

1. The script prints the league-facing message to stdout.
2. The same content is written to `/tmp/distribute_<season>_w<NN>.txt`
   so you can re-paste from the file if the terminal scrollback is
   inconvenient.
3. The script blocks on a confirmation prompt on stderr.
4. **Paste the message into the group thread.**
5. Return to the terminal. Press Enter to confirm and write the
   archive, or type `no` to abort without archiving.

## Commit step

The script prints this template after the archive write:

```
git add archive/recaps/
git commit -m "archive: distribute season 2025 week 7 v1"
git push origin main
```

The commit message convention is
`archive: distribute season <S> week <W> v<V>`.

## Verifying exit criterion #4 (a real member has read the recap)

"Read" means evidence of reception within 7 days of distribution:

- A reply.
- A reaction.
- An unprompted reference to the content (in the thread, in person).

Record each observation as it happens via the reception capture
runbook (`docs/runbooks/reception_capture_v1.md`). Any recorded
`reply`, `reaction`, or `reference` closes exit criterion #4.

If the 7-day window closes with no reception observations, file a
`silence_period_close` via `record_reception.py
--silence-window-close` and write the suggested `_observations/`
memo. Silence around a Writer's Room piece is information; the
silence-close record plus the memo capture it for voice-iteration
consideration in Track C.

## Failure modes

### No APPROVED artifact found

Exit code 3. The script's stderr names the actual state of the most
recent version (`DRAFT`, `WITHHELD`, `SUPERSEDED`).

Do not modify the script's behavior to permit distributing non-APPROVED
artifacts. Fix the upstream state instead — either approve the draft
per the Heuristic, or accept that this week is WITHHELD and there is
nothing to distribute.

### No artifact at all for the requested week

Exit code 2. Confirm the week is correct; confirm ingest and selection
ran. The lifecycle, not this script, is the place to fix this.

### APPROVED artifact has no extractable narrative

Exit code 4. The artifact is in `APPROVED` state but
`extract_shareable_parts` returned an empty narrative. This is a
defect — APPROVED implies the artifact passed the Heuristic and the
verifier, both of which require non-empty rendered output. Open an
observation memo and re-render the week before distributing.

### Archive entry already exists

Exit code 5. The append-only invariant forbids overwriting. The
existing file is the canonical record of distribution.

If the original distribution failed silently (paste went into the wrong
thread, etc.), do **not** edit the archive. Instead:

1. Resend manually if appropriate.
2. Write an `_observations/` memo recording what actually happened.

The archive frontmatter remains the engine's record of what it sent;
operational reality reconciliation belongs in observation memos.

### Commissioner aborts before pasting

Exit code 6 on graceful `no`, exit code 130 on Ctrl-C. The script
exits without writing the archive. Re-run when ready. No state
mutation persists from the aborted attempt.

### Paste went into the wrong thread

The archive has already been written by the time you discover this.
Treat as the previous case: do not edit the archive, write an
observation memo, and resend manually if appropriate.

### `--confirm-pasted` was used and the paste hadn't actually happened

The archive is written under the assumption that distribution
succeeded. If discovered before commit, manually delete the unstaged
archive files and re-run. If discovered after commit, write an
observation memo — the archive's `distributed_at` is then an
inaccurate record, but editing it would violate the append-only
invariant.

`--confirm-pasted` exists for testing and the rare case where you
genuinely paste-then-confirm without leaving the terminal. Use with
care.

## What this runbook does not include

- Engagement metrics or analytics — forbidden by the Platform
  Guardrails.
- Automatic re-distribution after failure — distribution is a
  human-approved act each time.
- Silent revision of distributed artifacts — see the append-only
  invariant.
- Anything that changes APPROVED-and-distributed state.

If a future session adds a new distribution channel (an AppleScript
hook driving Messages.app, an MFL commissioner-message handler, an
email handler), this runbook needs a corresponding section per
channel. The script's `--channel` flag will become meaningfully plural
at that point; until then, `group_text_paste_assist` is the only
supported handler.
