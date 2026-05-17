# Cadence Failure-Mode Runbook (Track D)

**Filed:** 2026-05-16
**Track:** D (Operational Scheduler)
**Operational Plan ref:** v1.1 section 6 + section 8 Phase B

This runbook covers failure modes specific to the automated Tuesday ingest
cadence. It extends Operational Plan v1.1 section 6 (which covers content-level
failures) and Operational Scenarios v1.1 (which covers data and edge cases).
It does not replace those documents.

Cross-reference: docs/runbooks/scheduler_v1.md (installation and operation).

---

## Happy path (reference)

    Tuesday 10:00 AM    launchd fires run_weekly_ingest.sh
    Tuesday 10:01 AM    Ingest completes, log written to logs/ingest_<ts>.log
    Wednesday morning   Commissioner runs generate_wednesday_digest.py
    Wednesday           Commissioner reviews digest, commissions recap
    Thursday-Friday     Commissioner approves via Recap Review Heuristic
    Friday-Saturday     Commissioner distributes via distribute_recap.py

Any deviation from this sequence is a failure mode. The runbooks below
cover the most likely deviations.

---

## FM-1: Tuesday ingest did not run (machine was asleep or off)

**Detection:** Wednesday digest shows no ingest log, or log timestamp is
more than 7 days old.

    launchctl list | grep squadvault
    ls -lt logs/ingest_*.log | head -3

**Response:** Run manually from repo root.

    cd /Users/steve/projects/squadvault-ingest-fresh
    bash scripts/run_weekly_ingest.sh

launchd does not retry missed windows. Manual invocation is the only
recovery path. Run as soon as possible Wednesday morning before
generating the digest.

**Impact:** None to data integrity. Ingest is idempotent. A Wednesday
manual run produces the same result as a Tuesday automated run.

---

## FM-2: Ingest ran but exited non-zero

**Detection:** Digest shows exit code != 0, or launchctl shows non-zero
last exit code.

    launchctl list | grep squadvault
    cat logs/ingest_*.log | tail -40

**Response triage:**

    Exit 1 with ConfigError: missing MFL_SERVER or MFL_LEAGUE_ID.
    -> Check .env.local contains MFL_SERVER, MFL_USERNAME, MFL_PASSWORD.
    -> Confirm --league-id 70985 is present in run_weekly_ingest.sh.

    Exit 1 with network error / MFL API timeout:
    -> Wait 30 minutes and retry manually.
    -> MFL API is occasionally slow Tuesday afternoons during NFL season.

    Exit 1 with SQLite error:
    -> Check DB path: .local_squadvault.sqlite at repo root.
    -> Run: python3 -c "import sqlite3; sqlite3.connect('.local_squadvault.sqlite').execute('SELECT 1')"
    -> If DB is corrupted, restore from most recent git-committed state
       (canonical events are append-only; a restore loses only the
       most recent ingest, which can be re-run).

**Impact:** No data written. Safe to retry.

---

## FM-3: Digest shows ingest_status = no_new_rows unexpectedly

**Detection:** Ingest ran and exited 0, but inserted=0 when new data
was expected (e.g., post-game-week during NFL season).

**Response triage:**

    1. Check whether MFL has posted the week's results yet.
       MFL transaction data for a given week is typically available
       Tuesday morning, but sometimes delayed.

    2. Confirm the SEASON in run_weekly_ingest.sh matches the current
       NFL season year.

    3. Check that MFL_SERVER in .env.local is the correct server
       for league 70985 (www44.myfantasyleague.com at last check).

    4. If MFL data is confirmed available and ingest still shows
       no_new_rows, the events may already be in the DB from a
       prior run. Query:

           python3 <<'EOF'
           import sqlite3
           conn = sqlite3.connect('.local_squadvault.sqlite')
           cur = conn.cursor()
           cur.execute("""
               SELECT event_type, COUNT(*) as n
               FROM canonical_events
               WHERE league_id='70985' AND season=2026
               GROUP BY event_type ORDER BY n DESC
           """)
           for r in cur.fetchall(): print(r)
           EOF

**Impact:** Low. Data integrity is not at risk. The ingest is
idempotent; duplicate events are skipped by design.

---

## FM-4: Digest shows artifact state = DRAFT with no APPROVED version

**Detection:** Digest recommended action says 'Draft vN pending review.
No approved version yet.' for the current week.

**Response:** This is normal if the recap has not yet been through
the approval flow. Follow the standard approval flow:

    ./scripts/py src/squadvault/consumers/recap_week_render.py ...
    ./scripts/py src/squadvault/consumers/editorial_review_week.py ...
    ./scripts/py src/squadvault/consumers/recap_week_approve.py ...

Refer to docs/runbooks/distribution_v1.md for the full approval flow.

---

## FM-5: Digest shows trailing DRAFT above an APPROVED version

**Detection:** Digest shows 'Newer draft vN above approved vM.'
This is the W18/W17/W16... pattern visible in the 2025 season data.

**Cause:** A recap was regenerated after approval, producing a new
DRAFT above the existing APPROVED row. The approved version is still
the canonical distribution record.

**Response options:**

    Option A: Distribute the existing APPROVED version.
    -> distribute_recap.py reads the latest APPROVED version, not
       the latest version overall. Distribution proceeds normally.

    Option B: Review and approve the newer DRAFT.
    -> Run the editorial review and approval flow on the new DRAFT.
    -> The new APPROVED version supersedes the prior one.

    Option C: Withhold the trailing DRAFT.
    -> If the DRAFT is not acceptable and the APPROVED version is
       the right take, withhold the DRAFT via recap_artifact_withhold.py.
    -> The APPROVED version remains the distribution target.

The Recap Review Heuristic governs which option is correct.
Operational pressure does not override the Heuristic.

---

## FM-6: launchd agent is not loaded after machine restart

**Detection:** launchctl list | grep squadvault returns nothing.

**Cause:** LaunchAgents in ~/Library/LaunchAgents/ load automatically
at login for the user. If the agent is absent, the plist may have
been removed, or the user session did not load it.

**Response:** Reload the agent.

    launchctl load ~/Library/LaunchAgents/com.squadvault.weekly-ingest.plist
    launchctl list | grep squadvault

If the plist file is missing, reinstall from the documented content
in the Track D session observation memo (2026-05-16) or
docs/runbooks/scheduler_v1.md.

---

## FM-7: Machine is off or unavailable for multiple weeks

**Detection:** Multiple weeks of missed ingest logs.

**Response:**

    1. When machine is available, run ingest manually:
       bash scripts/run_weekly_ingest.sh
       (The script ingests the full current season; all missed weeks
       are captured in a single run because ingest is season-level.)

    2. Generate digest to confirm catch-up state:
       ./scripts/py scripts/generate_wednesday_digest.py

    3. Decide whether to generate recaps for missed weeks.
       Per Operational Scenarios v1.1 section 3: missed weeks may
       be acknowledged explicitly or skipped entirely. No inference
       or gap-filling. Silence is preferred over speculative continuity.

**Impact:** Data integrity is preserved. The append-only invariant
means nothing is lost. Season-level ingest catches up in one run.

---

## Pre-season dry run checklist

Before Week 1 of the new NFL season, verify:

    [ ] SEASON in scripts/run_weekly_ingest.sh updated to new year
    [ ] Commit and push the SEASON update
    [ ] launchd agent loaded: launchctl list | grep squadvault
    [ ] .env.local present and contains MFL_SERVER, MFL_USERNAME, MFL_PASSWORD
    [ ] Manual dry run: bash scripts/run_weekly_ingest.sh
    [ ] Digest runs cleanly: ./scripts/py scripts/generate_wednesday_digest.py
    [ ] Digest shows ingest_status = no_new_rows (expected pre-season)
    [ ] logs/ directory exists and is writable
    [ ] DB path confirmed: .local_squadvault.sqlite at repo root

Run this checklist the week before the NFL season opener (~2026-09-01).
