# Session Brief -- Verifier Consistency and 2025 Regen Failure-Rate Investigation

Date prepared: 2026-06-06
Session type: Investigation / diagnostic. Why does regenerating approved 2025 weeks fail
verification on roughly two of three attempts? Establish verifier determinism (largely
pre-answered below), then characterize and attribute the failure rate. Produces a findings memo
with NUMBERED remediation options for decision. Diagnose only -- no verifier rewrite, no pipeline
change without sign-off.
Engine HEAD at handoff: 581dd6a (calibration memo on top of f48c4ba / e794575). CONFIRM in verify-first.
Repo: weichert/squadvault -- local ~/projects/squadvault-ingest-fresh.
Live DB: ./.local_squadvault.sqlite (WAL mode; seasons 2022/2024/2025; canonical_events ~38983;
70985 voice row live, len 3938).

---

## Why this session exists

The voice-quality calibration pass (memo OBSERVATIONS_2026_06_06_VOICE_QUALITY_CALIBRATION_PASS.md,
commit 581dd6a) found two things underneath the voice question:
- Finding A: regenerating already-approved 2025 weeks fails verification on ~2 of 3 attempts,
  and the failure is voice-INDEPENDENT (voice-off failed at least as often).
- Finding B: the verifier appeared to give divergent verdicts on an identical "5-game streak"
  claim (passed voice-on W16, failed voice-off W16).

Finding B gates Finding A: a failure-rate diagnosis cannot be trusted until the verifier is known
to be consistent. This session settles that, then investigates the rate.

ADVANCED DURING BRIEF PREP (gift to the next instance -- still confirm, but it reframes the work):
The verifier is DETERMINISTIC. src/squadvault/core/recaps/verification/recap_verifier_v1.py imports
only json, re, dataclass, and two internal modules (score_strings_v1, DatabaseSession). A scan for
nondeterminism sources (random / uuid / datetime.now / time / anthropic / messages.create / model= /
requests / httpx) returns ZERO. It is pure regex + DB lookups (5042 lines).

Therefore Finding B is NOT nondeterminism. It is a STREAK detector phrasing-coverage gap.
_STREAK_PATTERN (around line 1430) matches two forms only:
  (1) "<count>-game (win|winning|losing) (streak|skid)"  e.g. "five-game win streak"
  (2) "(won|lost|losing) <count> (straight|consecutive|in a row)"  e.g. "won five straight"
The voice-on W16 rendered text said "win streak to five games" -- the count TRAILS the noun, so it
matches neither branch and evades the check entirely (passes). Voice-off run 1 phrased it as a
leading-count form the pattern catches, so the check fired and flagged 5 vs actual 7/6. Same false
"5", different phrasing, deterministic verifier. Implication unchanged and important: a "passed"
verdict does NOT guarantee streak-claim correctness, because a fabricated streak can be phrased to
evade the detector.

Consequence for sequencing: the determinism probe below is CONFIRMATION, not discovery. Keep Phase 1
short. The real work is Phase 2 (the failure-rate investigation), which is now trustworthy precisely
because the verifier is deterministic.

---

## Verify-first (mandatory)

    git log --oneline -6      # confirm HEAD 581dd6a; calibration memo at top; tree clean
    git status

Then:
1. Confirm the calibration memo exists and is committed (581dd6a, doc-only, _observations/).
2. Re-set DB this session (it does NOT survive a new terminal): DB=./.local_squadvault.sqlite
3. Confirm the calibration voice-on DRAFTs are still REVIEW_REQUIRED, not approved: W1 v34,
   W8 v20, W16 v23. These are derived artifacts; leave them.
4. Stale-backlog discipline: verify every claim in this brief against git log and the code before
   acting. The picture moves; the deterministic-verifier claim above is from inspection of this
   commit and should be re-confirmed.

---

## The work (diagnostic-first per the dispatch model)

Phase 1 -- Confirm verifier determinism (short; mostly pre-answered).
1. Re-read recap_verifier_v1.py top matter; confirm no model/random/time/network (expected: clean).
2. Decisive isolation probe: run the verifier ALONE (NOT a regen) against ONE fixed narrative text
   N times (5x is plenty). Fixed input is the right isolation -- it separates verifier behavior from
   generation nondeterminism, which Finding B conflated by using different generations. Identical
   verdict every run confirms determinism. Use the W16 v23 rendered_text already in the ledger as
   the fixed input; trace the verifier entrypoint the lifecycle calls (weekly_recap_lifecycle.py
   into recap_verifier_v1.py) and feed it directly.
3. Demonstrate the STREAK gap concretely (converts Finding B from inference to demonstration): feed
   "win streak to five games" and "five-game win streak" through the same (season, week) verifier
   call and show one evades and one fires.

Phase 2 -- Characterize and attribute the failure rate (the real work).
1. The verifier is deterministic, so the failure rate is driven by GENERATION: the model fabricates
   different facts per run. Pull prompt_audit rows for the calibration generations
   (SQUADVAULT_PROMPT_AUDIT=1 was forced during that regen) and inspect what the model RECEIVED
   (facts block, system prompt) versus what it PRODUCED.
2. Categorize the fabrications: FAAB dollar/attribution, superlative/record, streak length,
   championship count, aggregate counts. Which dominate? Do they correlate with weeks carrying more
   FAAB / history events in context? (The calibration data hinted FAAB-dense and history-dense
   weeks fail more, but n was tiny -- get a real read.)
3. Regression vs tightening vs model drift: the April-approved-passes / now-fails comparison is
   CONFOUNDED (verifier changed since April, e.g. DRAFT_AUCTION_DOLLAR at 84564a4). Check whether
   prompt_audit retains April rows for these weeks; if so, diff what the model received then vs now.
   Check whether the model string behind the API changed (creative_layer_v1 model constant; any
   bump since April). Resolve as far as the data allows; an honest "undetermined" is acceptable.
4. Quantify properly: is ~2/3 stable, or an artifact of n=9? Sample more weeks with a few runs each
   to get a real rate. Each run is an API call -- budget it. If a full pass would exceed ~30
   generations, propose a sampling plan rather than brute-forcing (Research-feature-style discipline).

Phase 3 -- STOP and report as numbered options.
Remedies are DECISIONS, not in-session fixes, and several touch the integrity layer:
  - Detector-coverage hardening (e.g. STREAK trailing-count phrasing) -- needs its own test coverage.
  - Facts-block enrichment so the model has the streak / championship / FAAB values to cite
    (this is the project's own data-layer-over-prompt lesson: give it the number and it cites it;
    withhold it and it invents). Likely the highest-leverage remedy if fabrication tracks
    missing-from-context values.
  - Model pinning, if drift is implicated.
Propose; do not apply.

---

## Deliverable

- Findings memo OBSERVATIONS_<date>_VERIFIER_CONSISTENCY_AND_FAILURE_RATE.md (split if it grows):
  determinism confirmation, the STREAK phrasing-gap demonstration, the failure-rate
  characterization and attribution, and NUMBERED remediation options for decision.
- Doc-only commit to _observations/ (skips prove_ci.sh). Deliver via clean file download + place +
  verify byte count, same flow as the calibration memo.

---

## Scope boundaries (non-goals)

- No verifier rewrite. This investigates and proposes. Detector changes touch the integrity layer
  and require sign-off plus their own tests.
- No pipeline or model change without sign-off.
- No ledger writes. Regen appends derived DRAFTs only; facts are immutable and append-only.
- The W16 streak correction stays PARKED until the verifier is trusted and the true streak is
  established with certainty. Correction path is append-a-corrected-version, never edit the
  immutable April row.
- Not a voice session. The voice-quality verdict remains deferred (calibration follow-on 3) until
  weeks pass verification and there is output to judge.
- No analytics / optimization / engagement framing. Failure-rate is integrity diagnostics, not a
  metric to optimize. (Operational Plan section 10.)

---

## Stop-and-report checkpoints

- After Phase 1: report determinism confirmed (or, surprisingly, not) and the STREAK gap
  demonstrated. If it is somehow NOT deterministic, STOP and report -- that reframes everything and
  becomes its own session.
- After Phase 2 attribution: report the characterization and the regression-vs-tightening-vs-drift
  call (or honest "undetermined") BEFORE proposing remedies.

---

## Carry-forward gotchas (these cost real time this pass)

- Both repos prompt as "squadvault %". Confirm directory before work: engine has src/squadvault;
  frontend answers grep '"dev"' package.json.
- DB= does NOT survive a new terminal session -- re-set it first thing.
- zsh treats "?" in a sqlite URI as a glob ("zsh: unknown file attribute: h"). In heredocs use a
  plain-path connect (sqlite3.connect(path)), not file:...?mode=ro; or single-quote the URI.
- WAL mode: run PRAGMA wal_checkpoint(TRUNCATE) on the real DB before any filesystem copy, or the
  copy misses recently-written tables (league_voice_profiles was missing until checkpointed). The
  backup() API from a fresh read-only connection also missed the WAL this pass. Reliable control
  copy: checkpoint -> cp to /tmp -> delete the voice row in the COPY -> verify recap_runs>0 and
  voice=0 BEFORE regen.
- BSD grep has no -P. ASCII probe on macOS: LC_ALL=C grep -n '[^[:print:][:space:]]' file.
- Memo writes: pathlib write_text with a triple-quoted ASCII string; NO triple-backtick fences
  (they fragment in zsh heredocs). Self-test for non-ASCII before delivery; verify byte count after
  placing on disk (do not trust chat-rendered echoes).
- regen tool requires ANTHROPIC_API_KEY: set -a; source .env.local; set +a. It forces
  SQUADVAULT_PROMPT_AUDIT=1 on.
- Doc-only commits to _observations/ skip prove_ci.sh; pre-commit gates are
  banner/xtrace/repo-root/docs-map only (NOT ruff or pytest).

---

## One-line kickoff for the next session

The calibration pass found ~2/3 of 2025 regens fail verification, voice-independent, and that an
identical false "5-game streak" claim passed once and failed once. The verifier is deterministic
(confirmed by inspection: recap_verifier_v1.py is regex + DB only, zero nondeterminism sources),
so that divergence is a STREAK regex coverage gap -- trailing-count phrasing ("win streak to five
games") evades _STREAK_PATTERN -- not nondeterminism. Confirm determinism with a fixed-input
probe, demonstrate the STREAK gap, then characterize and attribute the ~2/3 failure rate via
prompt_audit (regression vs tightening vs model drift; the April-vs-now comparison is confounded).
Diagnose only; numbered remediation options; no verifier rewrite, no ledger writes. Verify HEAD
581dd6a and re-set DB=./.local_squadvault.sqlite first.
