# Observations — Track A first distribution (2026-04-28)

## Summary

Track A — distribution + archive loop on top of approved recaps —
shipped today. The first real distribution under the new flow landed
in the PFL Buddies group text thread: Season 2025 Week 7, artifact
v27, archived at `archive/recaps/2025/week_07__v27.md`.

This closes 4 of 5 IRP MVP exit criteria. Criterion #4 (a real PFL
Buddies member has read the recap) opens a 7-day reception window
ending approximately 2026-05-05. Pending the close of that window,
**MVP per IRP definition is met for the first time**.

Roughly 18 months of architecture, governance design, verifier
development, and lifecycle plumbing converged today into a paragraph
pasted into a group thread. That paragraph is the first time the
engine and the league actually met. Whatever comes back from the
thread over the next 7 days is the beginning of the post-MVP product.

## What shipped

- **Code commit:** `78a1aff` — Track A: distribution + archive loop
  (paste-assisted, append-only). 5 files, 818 insertions, 5 deletions.
- **Archive commit:** `2f7d583` — first archived distribution.
- **Files added:**
  - `scripts/distribute_recap.py` (482 lines) — paste-assisted
    distribution. Read-only DB access; no engine state mutation.
  - `archive/recaps/README.md` — append-only invariant + layout.
  - `docs/runbooks/distribution_v1.md` — commissioner runbook.
  - `Tests/test_archive_layout_v1.py` (4 tests, vacuous when empty,
    tightening as archive fills).
  - `Tests/test_repo_root_allowlist_v1.py` — added `archive` to
    `ALLOWED_ROOT_DIRS`; dropped unused `pytest` import en passant.
- **Test baseline:** 1816 passing / 2 skipped (was 1812 / 2 pre-Track
  A; +4 from the new layout tests).
- **Ruff / mypy:** clean across the enforced scope (`src/` for ruff;
  `src/squadvault/core/` for mypy). The new script also passes mypy
  as a bonus.
- **`prove_ci.sh` standing-items baseline:** reproduces identically
  pre- and post-Track A. Zero regression. The standing items remain:
  `_status.sh` missing, 6× `memory_events` allowlist violations,
  Docs integrity gate self-referential coverage gap, 3× `Voice
  variant rendering retired`, `gate_contract_linkage_v1.sh` missing,
  `pfl.registry` ModuleNotFoundError.

## The W7 distribution

- **Artifact ID:** v27.
- **Approved:** 2026-04-28T~22:51Z by `weichert`.
- **Selection fingerprint:**
  `5d2c813d8b0e421a4c2978406666963ddcfd0fc26e87f273a2860ac79`.
- **Window:** 2025-10-19T17:00:00Z → 2025-10-26T17:00:00Z.
- **Channel:** `group_text_paste_assist` (paste into existing PFL
  Buddies group text thread).
- **Distributed_to:** `league_channel`.
- **Archive entry:** `archive/recaps/2025/week_07__v27.md` and
  `.json`.
- **Reception window:** opened 2026-04-28; closes ~2026-05-05.

## The W7 lifecycle saga

The distribution was not the first attempt at W7. The append-only
ledger records 27 versions of the W7 artifact. Highlights of the
lifecycle:

- **v1–v23:** the normal pre-2026-04-09 working pattern. Multiple
  APPROVED → SUPERSEDED cycles (v4, v7, v11, v13, v14, v16, v19,
  v21), reflecting standard creative iteration where each new
  approval correctly superseded the prior one.
- **v24 APPROVED 2026-04-09T00:20Z.** The last approval that stuck
  before today.
- **v25 / v26 / v27 (DRAFT) created in a 64-minute burst on
  2026-04-14** between 09:00–10:04 UTC. None of these were approved
  at creation time. This date matches the
  `OBSERVATIONS_2026_04_14_Q4_SUPERLATIVE_DIAGNOSIS.md` and
  `OBSERVATIONS_2026_04_14_SUPERLATIVE_WIDER_PASS.md` diagnostic
  sessions in `_observations/`. The 4/14 burst was creative-layer
  iteration during diagnostic work, not factual re-ingest — all
  four versions (v24/v25/v26/v27) share the same selection
  fingerprint, so the underlying facts are identical across them.
- **v24 was orphaned** by the 4/14 DRAFTs. Append-only semantics
  meant the `ORDER BY version DESC LIMIT 1` head-of-version query
  returned v27 (DRAFT), not v24 (APPROVED), and the distribution
  script correctly refused to ship.
- **Resolution today:** reviewed v27 against the Recap Review
  Heuristic, approved. The lifecycle correctly transitioned v27
  DRAFT → APPROVED and v24 APPROVED → SUPERSEDED, syncing
  `recap_run` state. v27 then shipped.

## Findings

### F1 — v25 is a degenerate render (bug or gap, exact category TBD)

W7 v25 has length 2572 but the shareable narrative is just the
`SquadVault Weekly Recap` header line with no body content underneath.
Versions v24, v26, v27 all have substantive narratives (4032–4552
chars). The selection fingerprint is identical across all four, so
the same facts went in.

This is either:
1. A facts-only fallback path that produced an empty narrative
   (legitimate behavior given the diagnostic context, but the
   verifier should arguably reject "narrative is just the header"),
   or
2. A creative-layer or verifier gap that allowed an effectively-empty
   render to be persisted as DRAFT instead of being rejected outright.

Either way, the distribution gate caught it (would have refused to
ship v25 even if it had been APPROVED, because
`extract_shareable_parts` would have returned an empty narrative and
the script would have exited 4). The defense-in-depth worked. The
upstream cause is worth a future session.

**Action:** investigate in a future session, possibly as part of
Track C (voice iteration tooling) since it would naturally surface
this kind of pathology when comparing renders across versions.

### F2 — Runbook DB-path placeholder vs. canonical reality

`docs/runbooks/distribution_v1.md` uses `data/squadvault.db` as the
example invocation. My actual canonical DB is
`.local_squadvault.sqlite` at repo root. The mismatch caused a real
friction point (a `sqlite3.OperationalError: unable to open database
file` on the first distribution attempt).

**Action:** small doc fix — either correct the path to
`.local_squadvault.sqlite`, or change to `<PATH_TO_DB>` to make
substitution explicit. Defer to next operational session.

### F3 — Stale sibling clone: `~/projects/squadvault-ingest/`

A second clone exists at `~/projects/squadvault-ingest/` (without
`-fresh` suffix). Its `.local_squadvault.sqlite` is 2.6MB, last
modified 2026-02-02, throws disk I/O errors on read. The canonical
clone is `~/projects/squadvault-ingest-fresh/` (51MB DB, last
modified 2026-04-20, queries cleanly).

**Action:** confirm nothing in `~/projects/squadvault-ingest/` is
salvageable; archive or delete. Not urgent but creates search noise
during DB-path resolution.

### F4 — Commit-message version drift

The Track A archive commit was typed as
`archive: distribute season 2025 week 7 v1`, but the actual archived
artifact is v27 (`week_07__v27.md`). The script's printed template
correctly said "v27"; the "v1" came from a stale example in
conversation that didn't account for the real version.

**Procedural lesson:** future commit messages for archive
distributions should pull the version directly from the script's
printed template, not from any pre-stubbed example. Worth carrying
into the next session's prompt.

### F5 — Missing "promote prior APPROVED forward" semantic

The W7 lifecycle resolution today required reviewing and approving
v27 because the lifecycle has no operational pattern for "v24's
content is canonical, please promote it forward as v28 without
content change." The append-only invariant is correct in principle,
but in cases where multiple DRAFTs accumulate after an APPROVED row
and the prior APPROVED is still the right take, the operational
options today are:

1. Approve the latest DRAFT (today's path, when the latest DRAFT is
   acceptable).
2. Regenerate via creative layer (uncertain output, identical facts).
3. WITHHOLD the trailing DRAFTs (does not unblock distribution; the
   script reads `ORDER BY version DESC LIMIT 1` and would still see
   a non-APPROVED head).

For W7 today, option 1 worked because v27's prose was acceptable per
the Heuristic. If it hadn't been, the operational path would have
been awkward. Worth thinking about as a future Operational Scenarios
revision — possibly a `promote-version` lifecycle action that creates
a new APPROVED row carrying forward an explicitly-named prior
version's content. **Not for this session, just flagged.**

## What worked

A few observations on the design choices that paid off today:

- **Reuse of `extract_shareable_parts`** instead of duplicating
  delimiter logic kept the distribution script honest to the
  lifecycle's existing contract. When the contract changes,
  distribution evolves in lockstep.
- **Read-only DB access** kept distribution from accidentally
  mutating engine state during the multiple aborted attempts (DB path
  errors, lifecycle refusals). The state at the start of the
  successful run was the same as the state at the start of the first
  attempt.
- **The script's strict "latest must be APPROVED" gate** correctly
  refused to ship v27 in DRAFT and explicitly named the version. That
  refusal was the proximate trigger for the lifecycle resolution that
  produced today's clean ship.
- **The paste-assist channel** kept human-approves-publication
  literally inside the distribution loop. The terminal prompt is the
  last point at which the commissioner can say "no" — and the
  threshold for "no" is correctly low (anything looking off in the
  paste preview, wrong thread, formatting munged).
- **Frontmatter as the canonical distribution record** (vs. a
  separate `recap_distributions` table) proved its simplicity-first
  case immediately. The archive directory is the operational truth
  about what was distributed and when. No coordination between two
  stores for one operational fact.

## Reception observation (pending)

The 7-day window opened 2026-04-28 and closes approximately
2026-05-05. Per the runbook, "read" means evidence of reception:

- A reply in the thread.
- A reaction.
- An unprompted reference (in the thread, in person).

If any of those occurs, exit criterion #4 closes positively. If
silence, the closure is a finding — silence around a Writer's Room
piece is information about the league's relationship to the output,
not a failure of the distribution mechanism.

This memo will be updated with an addendum within 7 days recording
what was observed.

## MVP-complete declaration (conditional)

Conditional on the close of exit criterion #4 within the 7-day
window, MVP per IRP definition is met as of 2026-04-28. The IRP
definition has been the operational target since the project's
inception. This is the first time it has been satisfied.

---

## Addendum log

*This section will accrete reception observations and any subsequent
findings related to the W7 distribution. Format: dated entries,
append-only, no silent revision.*

### 2026-04-28 — distribution sent

Distribution executed. Awaiting reception observations.
