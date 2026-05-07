# OBSERVATIONS — Player-streak verb inversion diagnostic (Step 0b)

**Drafted:** 2026-05-06.
**HEAD at run:** a56cf1b (harness commit immediately preceding this memo).
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 0b of the diagnostic-first session
described in
`_observations/session_brief_player_streak_verb_inversion_diagnostic.md`
(`afec7b6`). Companion to the Step 0a harness commit `a56cf1b`.

---

## TL;DR

- **GATE: CLOSE.** Across the 18-row approved 2025 corpus, the
  per-claim classifier registered zero specimens in any
  integrity-tier or editorial-tier category. Standing-backlog
  item #5 closes with the conditional-reopening clause specified
  in the brief.
- **54 canonical player-streak claims** fired (P1=14, P2=30,
  P3=10). 16 surfaced into prose as CORRECT; 38 registered as
  NO_CLAIM (no player-name reference in prose). The
  silence-over-speculation principle treats NO_CLAIM as coverage
  measurement, not failure.
- **Re-promotion remains conditional.** "No evidence in current
  corpus" is not "no possible evidence". W14+ live observation
  per the post-§10 Q1 development direction may surface
  specimens; if it does, the four-step playbook re-opens with
  this harness as step-0 instrumentation.

---

## 1. Why this session

The team-streak verb-inversion thread (`6e7d44a` / `71d6e5f` /
`7d891aa`) shipped the four-step playbook for status-verb
inversions on team W-L streaks. Its scope memo §3.2 explicitly
named three player-level emitters as out-of-scope on the
rationale that "player-level streak" is a different sense of the
word. The promotion criterion was empirical:

> If post-Step-3.3 measurement shows player-streak verb
> inversions in the wild, those become a separate four-step
> thread.

This session is the empirical arbiter. Diagnostic-first; no
production code changes regardless of outcome. Brief is at
`afec7b6`.

---

## 2. Harness output

Run command:

    scripts/py scripts/diagnose_player_streak_verb_inversions.py \
      --db .local_squadvault.sqlite --league-id 70985 --season 2025

Corpus: 18 approved 2025 weekly recaps from `recap_artifacts`
(state='APPROVED', league_id='70985'). Memory note had recorded
"35 approved recaps" from a prior session; actual count at this
run is **18**. Memory-vs-actual drift on corpus size is a
recurring hazard worth recording.

Total canonical claims: 54 across the three emitters.

| Emitter | Detector | Claims | DIR_INV | FR_MIS | TH_INV | TEN_NC | DUR_DRIFT | CORRECT | NO_CLAIM |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P1 | `detect_player_hot_streak`       | 14 | 0 | 0 | 0 | -- | 0 |  5 |  9 |
| P2 | `detect_player_cold_streak`      | 30 | 0 | 0 | 0 | -- | 0 | 10 | 20 |
| P3 | `detect_player_franchise_tenure` | 10 | 0 | 0 | -- | 0 | 0 |  1 |  9 |
| **Total** |                          | **54** | **0** | **0** | **0** | **0** | **0** | **16** | **38** |

(P1/P2 do not have a TENURE_NON_CONSECUTIVE bucket; P3 does not
have a THRESHOLD_INVERSION bucket since it has no scoring
threshold.)

Integrity-tier total: 0
Editorial-tier total: 0

---

## 3. Specimen analysis

Per the brief's Section 5, specimen analysis is required only
for non-zero integrity- or editorial-tier classifications. With
all such buckets at zero, no specimens are extracted into the
memo body.

For methodological transparency, the 16 CORRECT classifications
distribute as follows:

- **P1 hot streaks** -- 5/14 surfaced into prose, all paraphrasing
  the canonical "scored {N}+ points in {M} consecutive weeks"
  form without semantic loss.
- **P2 cold streaks** -- 10/30 surfaced, all preserving the "under
  {N} in {M} straight starts" structure or its
  direction-equivalent paraphrase.
- **P3 tenure** -- 1/10 surfaced. This is the structurally
  expected outcome. P3 emits at strength=1 (MINOR per
  `player_narrative_angles_v1.py:1336`); it is the lowest-
  priority player angle and is least likely to survive
  HEADLINE/NOTABLE budget eviction in any given week.

**Silence-rate observation.** 38/54 (70%) of canonical claims
went unmentioned in prose. This is consistent with -- not
contradicted by -- the silence-over-speculation principle.
Player-streak claims compete with team-level angles, fabrication-
risk headline angles (record claims, season-context flips), and
the recap's narrative throughline for budget. The model dropping
claims it can't anchor to the narrative is the desired behavior.
The high silence rate also explains why direction-inversion
fabrication is structurally harder for player-streaks than
team-streaks: the surface area for inversion is narrow because
the surface area for surfacing at all is narrow.

**Known limitation.** The harness uses full-name then last-token
(>=4 chars) for player-name resolution. Oblique references
(pronouns, position-based phrasing, short last names) would
register NO_CLAIM even if an inversion were present in those
references. Documented in the harness module docstring; the
18-row corpus is small enough for manual spot-check if a future
re-run wants name-resolution coverage verification, and the
harness could be extended with a `--debug-no-claim` flag for
that purpose. Out of scope for this session per the brief's
binary integrity/editorial gate framework.

---

## 4. Decision

**GATE: CLOSE.** Per the brief's two-tier evidence gate:

- *Integrity tier* (DIRECTION_INVERSION, FRANCHISE_MISMATCH,
  THRESHOLD_INVERSION, TENURE_NON_CONSECUTIVE): zero specimens.
  No integrity-tier ship signal.
- *Editorial tier* (DURATION_DRIFT): zero specimens. No
  editorial-tier elect signal.
- *Disposition:* close standing-backlog item #5 with the
  conditional-reopening clause specified in the brief's Q3.

Standing-backlog item #5 closure language:

> Closed at this commit. Empirical: zero integrity- and
> editorial-tier specimens across 54 canonical P1/P2/P3 claims
> in the 18-row 2025 approved corpus. 38/54 (70%) silence rate
> is consistent with silence-over-speculation discipline.
> **Conditional reopening:** if W14+ live observation per the
> post-§10 Q1 direction surfaces a player-streak verb-inversion
> specimen, re-open with this harness as step-0
> instrumentation. The harness is preserved in `scripts/` for
> that purpose.

---

## 5. Methodology notes for the session record

A few observations worth preserving:

- **Memory-vs-actual corpus size drift.** Memory recorded "35
  approved recaps"; actual is 18. A reverify against
  `recap_artifacts` at session start is cheap insurance against
  citing stale numbers in subsequent memos.

- **§10 Q1 harness filename heterogeneity.** Memory referred to
  "the §10 Q1 fabrication-shape harness" without filename; the
  expected location was `scripts/diagnose_*.py` based on recent
  diagnostic naming convention. Actual filename is
  `scripts/step_1_streak_diagnostic_harness.py`. Future
  grounding should use content-grep against the harness's
  characteristic tokens (e.g., `RECORD_APPROACH`,
  `STATUS_CLAIM_OMITTED`), not filename-prefix patterns.
  `scripts/` now contains at least four naming families:
  `diagnose_*`, `step_1_*`, `verify_*`, and probes
  (`notable_saturation_probe.py`, etc.).

- **No counterfactual reconstruction needed.** The §10 Q1
  harness required counterfactual reconstruction because
  `prompt_audit.angles_summary_json` strips `franchise_ids` and
  `headline` per `prompt_audit_v1.py:174`. The player-streak
  orchestrator (`detect_player_narrative_angles_v1`) takes
  `(db_path, league_id, season, week)` and loads its own data,
  so this harness calls the orchestrator as a black box.
  Cleaner shape than the team-streak case; a useful precedent
  for future detector-orchestrated diagnostics.

- **Alias-naive FRANCHISE_MISMATCH detector.** Documented in the
  module docstring. Zero hits in this run; if hits surface in a
  future run, the detector should be extended via the Option B
  nickname-override layer (`migration 0010`,
  `_build_reverse_name_map` pass 4a/4b at
  `recap_verifier_v1.py`).

- **Recovery-from-paste-error.** This session's commit pair was
  reconstructed from a single accidental commit (`69e712b`
  on origin) where the harness file landed under the memo's
  intended message due to zsh fragmenting the apply block on an
  inline-comment hazard. Recovered via `commit --amend` +
  separate memo commit + `push --force-with-lease`. The
  one-topic-per-commit discipline holds for the final history;
  the brief diversion is recorded here for honest trail.

---

## 6. Files and commits referenced

- `scripts/diagnose_player_streak_verb_inversions.py` -- Step 0a
  harness (commit `a56cf1b`).
- `_observations/session_brief_player_streak_verb_inversion_diagnostic.md`
  (`afec7b6`) -- session brief.
- `_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
  §3.2 -- promotion criterion.
- `6e7d44a` / `71d6e5f` / `7d891aa` -- team-streak four-step
  thread (precedent for the playbook this session would have
  re-applied if the gate had said PROMOTE).
- `e4c2df8` -- Cat 3c hardening (record-claim attribution).
- `850478c` -- `scripts/step_1_streak_diagnostic_harness.py` with
  fabrication-shape classifier (precedent for diagnostic
  structure; orchestrator pattern of this harness differs and
  is simpler).
- `src/squadvault/core/recaps/context/player_narrative_angles_v1.py`
  -- emitters at lines 752-755 (P1), 804-807 (P2), 1330-1333
  (P3); orchestrator at line 2083.
- `scripts/verify_player_trend_detectors.py` -- orchestrator-call
  template (resolver construction at lines 222-228).
