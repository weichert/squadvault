# OBSERVATIONS 2026-06-06 -- Voice-Quality Calibration Pass (PFL Buddies)

Session type: Quality / calibration review (diagnostic only).
Engine HEAD at session start: f48c4ba (status reconciliation + calibration brief on top of e794575).
DB: ./.local_squadvault.sqlite (live ingest; seasons 2022/2024/2025; canonical_events 38983; 70985 voice row present, len 3938).
Scope respected: diagnose only, no voice rewrite, no ledger fact writes. See "Provenance" at end.

---

## TL;DR

The voice pipe is confirmed live and byte-faithful: the live 70985 voice row is identical to
the in-repo PFL_BUDDIES_VOICE_PROFILE constant (len 3938), and the creative layer injects it
before the hard-rules marker (governance-correct -- voice cannot override facts).

But the voice-quality question the brief scoped is largely unanswerable right now, because a
deeper, voice-INDEPENDENT problem sits underneath it: regenerating already-approved 2025 weeks
today fails verification on roughly two of every three attempts, voice on or off. The system
correctly falls back to facts-only (silence over fabrication is working), so nothing bad ships
-- but it also means most weeks produce no narrative to judge.

Two findings stand on their own and are flagged for dedicated follow-on sessions. The voice
verdict itself is provisional (n=1 clean pair) and deferred.

---

## Method

Sample: W1 (clean/FAAB-dense), W8 (streak/FAAB-dense), W16 (championship semifinal, FAAB-light).
Each week has a clean APPROVED "before" from April 2026 (W1 v0 approved 2026-04-14, W8 2026-04-14,
W16 2026-04-16), all predating the 2026-06-05 voice-live, so a fresh regen is the first
voice-injected output for each.

Regen tool: scripts/recap_artifact_regenerate.py (requires ANTHROPIC_API_KEY; forces
SQUADVAULT_PROMPT_AUDIT=1; appends a derived DRAFT, leaves APPROVED untouched, writes no facts).

Control: voice-off regen of the same three weeks, same day, same verifier, against a /tmp copy of
the DB with the 70985 voice row deleted (real DB untouched except a benign WAL checkpoint). Run
twice, giving 2 voice-off samples per week against 1 voice-on.

---

## The control grid (evidence)

| Week | voice-ON (1 run) | voice-OFF run 1 | voice-OFF run 2 |
|------|------------------|-----------------|-----------------|
| W1   | FAIL: SUPERLATIVE + FAAB_CLAIM | PASS (soft: ordinal 323) | PASS (soft: ordinal 323) |
| W8   | FAIL: FAAB_CLAIM | FAIL: FAAB_CLAIM | FAIL: FAAB_CLAIM |
| W16  | PASS | FAIL: STREAK + FAAB_CLAIM + CHAMPIONSHIP_CLAIM | FAIL: STREAK + CHAMPIONSHIP_CLAIM |

Failure detail (the fabrications were a moving target across runs):
- W1 voice-on: framed Lamar 35.45 as an all-time record (actual high 198.80 team / 77.00 player);
  attributed $15 FAAB to Quentin Johnston (actual $8.77 -- that $15 is Boutte's bid).
- W8: invented a different phantom FAAB acquisition every run -- Tucker Kraft (voice-on),
  Jalen Hurts (off run1), Tampa Bay Buccaneers (off run2). None acquired via FAAB.
- W16 voice-off: fabricated streak counts (Playmakers 5 vs actual 7/6; Warmongers 3 vs 5/4),
  a $60 FAAB for Justin Jefferson, and championship tallies (Playmakers 7 vs 6; Warmongers 2 vs 3).

Same-day voice axis (clean comparison): voice-off failed W8 twice and W16 twice, including weeks
that PASSED voice-on. Failures do not track the voice flag.

---

## Finding A -- Verification failure rate on 2025 regen is ~2/3, and it is voice-independent (LEAD)

Across 9 generations of weeks that already have APPROVED narratives in the ledger, the verifier
rejected the narrative on roughly two of three attempts, with no relationship to the voice flag.
The model confabulates FAAB dollars, streak lengths, superlatives, and championship counts on a
large fraction of runs; which fact it invents is random per generation.

These weeks were approved and published in April. So something changed between April and now:
the model behind the API, the verifier strictness, the facts/context block, or some combination.
This BEFORE-passed / AFTER-fails comparison is CONFOUNDED -- the verifier has changed since April
(e.g. DRAFT_AUCTION_DOLLAR category added at 84564a4, among others). Therefore this is NOT
cleanly a "regression"; it is "regression OR tightening OR model drift, undetermined." That
distinction matters and should not be collapsed.

This is a core-pipeline question, independent of and more urgent than voice calibration. It is
outside the calibration brief's scope. Recommend a dedicated session (follow-on 1 below).

## Finding B -- Verifier gives divergent verdicts on an identical claim (integrity concern)

Both the voice-on run and voice-off run 1 of W16 produced a Paradis' Playmakers "5-game win
streak" claim. The verifier flagged it HARD in voice-off run 1 (actual 7 current / 6 pre-week)
but did NOT flag it in the voice-on run, which PASSED. Identical claimed number, divergent
verdict across runs.

Implication: a "passed" verdict does not currently guarantee streak-claim correctness. The
voice-on W16 narrative that passed this session contains a likely-false streak figure ("five-game
win streak"); the April-APPROVED W16 already in the ledger contains the same "five-game win
streak" phrasing and may carry the same error. (The April approved row is a fact-immutable
published artifact; flag for review, do not alter -- correction path is append a corrected
version, never edit.)

Caveat: the voice-off claimed value is read from the verifier's parse ("Claimed: 5"), not from
its rendered text (which was not captured). The voice-on rendered text is captured and does say
"five games." The divergence is therefore well-supported but the mechanism (verifier
nondeterminism vs phrasing-sensitivity of the STREAK detector) is not yet established.

Recommend a dedicated verifier-consistency probe (follow-on 2 below). This is high-value: it
bears directly on the integrity guarantee that narratives never assert unverified facts.

## Finding C -- Voice quality: provisional, n=1, deferred

Only W16 produced a shippable on/off pair (both rendered a full narrative), so the voice read is
n=1 and provisional:
- WIN: voice landed the mandated historical hedge -- "across the last 15 seasons of available
  data" -- exactly the phrasing the directive requires. The April default-tone before said "across
  the last 15 seasons" without the hedge. Attributable to the voice directive.
- WIN (weak, n=1): voice-on got the championship count right (6), while both voice-off runs
  fabricated it (7, then 2). Suggestive that the directive's history emphasis may anchor rather
  than invent on history-heavy weeks -- but n=1, not a claim.
- MISS: otherwise the voice-on W16 reads close to default and still leans on columnist adjectives
  the rubric warns against ("explosion," "disaster," "cruised," "nail-biter," "blowout"). On the
  "let results speak through numbers, not adjectives / no TV cadences" axis (rubric sec 6), the
  voice did not land. This is the "snark in costume" risk the brief names; on n=1 it leans that way.
- CORRECT BY DESIGN: no forced group slang (no "schloppy"/"thrashed"). The directive deliberately
  says "use natural vocabulary where it emerges from the data" and does not enumerate sec 4 terms.
  The target bar is "someone who knows these people," not "one of them" (rubric line 184).

A real verdict needs weeks that pass verification, which loops back to Finding A. Voice verdict
deferred (follow-on 3).

## Finding D -- Directive naming rules are not steering output; sec 7 already violated at baseline

Both the voice-on AND voice-off outputs write "KP's Playmakers" and "Steve's Warmongers." The
live directive explicitly forbids both ("write 'Paradis' Playmakers' not 'KP's Playmakers'";
"never write 'Steve's Warmongers'"). First-name action phrases ("Steve left points on the bench")
also appear voice-off. Because these appear with voice OFF too, they are BASELINE behavior, not
voice-induced.

Two consequences:
1. The directive's most prescriptive, specific instructions (possessive grammar, team-names-on-
   first-reference) are being ignored by the model. This is the project's own "data-layer beats
   prompt guardrails" lesson reasserting: a possessive rule expressed as a prompt instruction is
   weak. If team-name grammar matters, it likely needs data-layer enforcement (pre-rendered
   canonical name strings), not a prompt directive.
2. Rubric sec 7 ("the system uses team names only," no real first names in recaps) is already being
   violated at baseline, independent of the voice row. The earlier-flagged sec 7 first-name tension
   is therefore not a voice question -- it is a baseline output question plus a founder policy
   question (team-names-only vs sanctioned first-name use). Founder decision pending (follow-on 4).

---

## Hypothesis retired

The prior-session hypothesis that the directive's FAAB and history emphasis was DRIVING the
fabrication (FAAB invented, records invented) is NOT supported by the control. Voice-off failed at
least as often, with the same failure categories. Retired -- do not carry forward.

---

## Recommended follow-on sessions (each its own brief; do NOT drift into them here)

1. Verification-rate investigation. Determine whether the ~2/3 failure rate is regression,
   tightening, or model drift. Pull prompt_audit / prompt_audit_reverify rows for these weeks,
   diff verifier categories April vs now, and check whether the model string behind the API
   changed. Candidates: verifier changes since 84564a4 (DRAFT_AUCTION_DOLLAR and others); model
   version; facts-block changes. Highest priority.
2. Verifier-consistency probe (STREAK first). Re-run a fixed week N times and check whether
   identical claims receive identical verdicts. If nondeterministic, that is a verifier integrity
   gap: passing does not currently guarantee claim correctness (Finding B).
3. Voice-quality verdict (deferred until weeks pass). Once Finding A is resolved so weeks ship,
   run the full 7-week on/off read against the rubric.
4. Naming / sec 7 founder decision. Team-names-only enforcement at the data layer vs sanctioned
   first-name use. Note the prompt directive alone does not enforce it (Finding D).

---

## Provenance and scope compliance

- Voice-on regen appended derived DRAFT artifacts to the live DB: W1 v34, W8 v20, W16 v23, all
  state REVIEW_REQUIRED, none approved. These are derived narratives, never fact-creating
  (append-only ledger invariant honored). No canonical_events / memory_events were written.
- Voice-off control ran entirely against /tmp/sv_novoice.sqlite (a copy). The only write to the
  real DB was PRAGMA wal_checkpoint(TRUNCATE), which flushes already-committed WAL pages into the
  main file and creates/alters no data.
- No voice rewrite. The directive was not changed. This pass diagnoses only.
- Doc-only deliverable. No core code changed.
