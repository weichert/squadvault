# Scheduler Runbook -- Weekly Ingest (Track D)

**Filed:** 2026-05-16
**Track:** D (Operational Scheduler)
**Operational Plan ref:** v1.1 section 8 Phase B

---

## What this is

A launchd agent (`com.squadvault.weekly-ingest`) runs
`scripts/run_weekly_ingest.sh` every Tuesday at 10:00 AM local time.
The script ingests the current season's transactions from MFL and
canonicalizes them into `.local_squadvault.sqlite`.

This automates the highest-risk manual step in the weekly pipeline.
The commissioner's remaining manual steps are: Wednesday review,
Thursday-Friday approval, and distribution.

---

## Platform decision

Local launchd (macOS). GitHub Actions was ruled out: the canonical
DB is `.local_squadvault.sqlite` on the local machine; a remote runner
cannot write to it without SSH-back-to-machine complexity that is more
fragile than the problem it solves.

---

## Ingest script behavior

- **Script:** `src/squadvault/ops/run_ingest_then_canonicalize.py`
- **Season-level:** ingests all transactions for the configured season,
  not per-week. The season is set once per year in the wrapper script.
- **Idempotent:** if no new rows exist, exits 0 with
  `ingest_status = no_new_rows`. Safe to run multiple times.
- **Required env vars:** `MFL_SERVER`, `MFL_USERNAME`, `MFL_PASSWORD`
  (from `.env.local`). `MFL_LEAGUE_ID` is passed as `--league-id 70985`
  explicitly (not in either .env file).

---

## Plist location (machine-local, not in repo)

    ~/Library/LaunchAgents/com.squadvault.weekly-ingest.plist

The plist is not committed to the repo. It is machine-local
configuration. The content is documented in the Track D session
observation memo (2026-05-16).

---

## Annual configuration update

At the start of each new NFL season, update SEASON in the wrapper:

    # Edit scripts/run_weekly_ingest.sh
    # Change: SEASON=2025
    # To:     SEASON=2026

Commit the change before the season's first Tuesday ingest.

---

## Checking whether last Tuesday's ingest ran

    ls -lt logs/ingest_*.log | head -3
    cat logs/ingest_*.log | tail -20
    launchctl list | grep squadvault

A `-` in the PID column means not currently running (expected).
The second column is the last exit code -- 0 means success.

---

## Manually triggering the ingest

If Tuesday's scheduled run is missed (machine was asleep or off):

    cd /Users/steve/projects/squadvault-ingest-fresh
    bash scripts/run_weekly_ingest.sh

launchd does NOT retry missed StartCalendarInterval windows at wakeup.
A missed Tuesday window stays missed. Manual invocation is the only
recovery path.

---

## Installing or reinstalling the plist

    launchctl load ~/Library/LaunchAgents/com.squadvault.weekly-ingest.plist
    launchctl list | grep squadvault

---

## Disabling the scheduler (off-season)

    launchctl unload ~/Library/LaunchAgents/com.squadvault.weekly-ingest.plist
    launchctl list | grep squadvault  # should return nothing

Re-enable at the start of the next season (update SEASON first, then load).

---

## Log locations

logs/ingest_<timestamp>.log  -- per-run output (ingest results, sanity checks, exit code)
logs/launchd_ingest.log      -- launchd stdout passthrough
logs/launchd_ingest_err.log  -- launchd stderr passthrough

Log files are excluded from the repo via .gitignore (logs/*.log).
logs/.gitkeep tracks the directory itself.
