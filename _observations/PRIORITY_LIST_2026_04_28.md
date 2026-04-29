# Priority list — re-grounding pass (2026-04-28)

## Purpose

This memo supersedes the drift in carried priority lists (userMemories,
session-brief candidate sets, prior session backlogs) and produces one
authoritative "what's actually open" list verified against the repo at
HEAD `60c4976`.

**Trigger.** A session was about to begin work on "Player Trend
Detectors T1" — the userMemories carried it as next priority. Direct
inspection of the repo found T1 (and T2–T11) already implemented in
`src/squadvault/core/recaps/context/player_narrative_angles_v1.py` and
verified firing in production by the 2026-04-09 observation memo. The
priority list was stale by ~3 weeks. Diagnostic-first discipline caught
it before any code was written.

This memo exists so the next session-start does not repeat the loss.

## Methodology

Cross-checked against the actual repo at `60c4976`:

1. Read `_observations/` memos chronologically from 2026-04-20 forward
   (the F-series finding triage and its closures).
2. Verified each putative "open" item by inspecting the file or
   running the relevant grep / ls / status check.
3. Marked items as CLOSED (with evidence), OPEN (with evidence), or
   UNVERIFIABLE-FROM-FRESH-CLONE (depends on local-only state like
   unpushed commits).

No item is asserted as CLOSED without a concrete repo-state check.

## What is CLOSED — drop from any priority list

These items have appeared in carried priority lists but are
demonstrably done. None of them is a candidate for a future session.

### Player Trend Detectors T1–T11 (D1–D11)

All 11 detectors implemented in
`src/squadvault/core/recaps/context/player_narrative_angles_v1.py`.
Verified by `Phase_10_Observation_T1_Verification_and_Trade_Loader_Bug.md`
(2026-04-09) — production firing rates T1=14/14, T2=30/30, T3=4/3,
T4=110/127, T5=55/53, T6=19/22 across 2024/2025 weeks. Diagnostic
script `scripts/verify_player_trend_detectors.py` exists in the repo.

### Trade-loader silent-zero bug (D4 / `_load_season_trades`)

Was bookmarked in the same 2026-04-09 memo as a new bug. Closed at
commit `39c8f1c` per
`Phase_10_Observation_NAv2_Verification_Streak_Momentum_and_Trade_Loader.md`.
Production firings 0 → 36 across both seasons after the bilateral
`_Trade` dataclass + `raw_mfl_json` extraction rewrite.

### Finding B triage F-series (F1 through F7)

The seven sub-findings from `OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`:

| Sub-finding | Status at HEAD `60c4976` | Evidence |
|---|---|---|
| F1 (process_full_season.sh shim) | CLOSED | 4× `./scripts/py` invocations; no `PYTHONPATH=src python3` |
| F2+F5 (registry machine block) | CLOSED | commit `a56c147` |
| F3 (patch_idempotence_allowlist retire) | CLOSED | commit `e358886` |
| F4 (fs ordering archive exclusion) | CLOSED | commit `d94132e` |
| F6 (gate_no_obsolete_allowlist retire) | CLOSED | per F6 retirement memo |
| F7 (rivalry contract Enforced By line) | CLOSED | doc has only the one extant script line |

### Findings B/C/D/E (new findings spawned during F-series closure)

All four were named in the 2026-04-27 F3 retirement memo as new
dormant-gate findings:

| Finding | Status | Evidence |
|---|---|---|
| Finding B (gate_prove_ci_structure_canonical) | CLOSED | per Finding B closure memo (`OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md`) |
| Finding C (registry index discoverability gate) | CLOSED | per `FINDINGS_C_E_RETIREMENT` memo |
| Finding D (LC_ALL portability) | CLOSED | per `FINDING_D_LC_ALL_PORTABILITY` memo |
| Finding E | CLOSED | per `FINDINGS_C_E_RETIREMENT` memo |

### Track A and Track B operational deliverables

- Track A — distribution loop closure: shipped today
  (`OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`).
- Track B — reception capture: shipped today
  (`OBSERVATIONS_2026_04_28_TRACK_B_RECEPTION_CAPTURE_SHIPPED.md`).

## What is OPEN — actual candidates

Categorized by character: hygiene/closure, engine, operational. Effort
estimates are rough.

### Hygiene / closure (small, low-risk, "while we wait" appropriate)

#### H1. Finding B mechanism closure — `set -euo pipefail` to `prove_ci.sh`

The triage and unblocking work is complete. The actual one-line
addition to `scripts/prove_ci.sh` (after the existing
`LC_ALL=C / LANG=C / TZ=UTC / PYTHONHASHSEED=0` envelope at lines 8–11)
is still pending. Verified at HEAD: `grep set -e scripts/prove_ci.sh`
returns nothing.

Per `OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md`: "Finding B mechanism
closure (`set -euo pipefail` addition to `prove_ci.sh`) is now safe to
land — there is no pre-existing silent-rc=1 gate for it to expose."

**Effort:** ~30 min. One-line edit, single commit, validate clean
`prove_ci.sh` rc=0.

**Why now:** unblocked since 2026-04-27, surface clean, this is the
natural cap on a multi-session workstream. Highest-leverage hygiene
item.

#### H2. Tests/ ruff cleanup (229 errors)

Verified breakdown at HEAD:

| Rule | Count | Auto-fixable |
|---|---|---|
| I001 unsorted-imports | 103 | yes |
| F401 unused-import | 89 | yes |
| F541 f-string-missing-placeholders | 13 | yes |
| F811 redefined-while-unused | 1 | yes |
| E702 multiple-statements-on-one-line | 9 | no |
| E731 lambda-assignment | 7 | no |
| E741 ambiguous-variable-name | 4 | no |
| F841 unused-variable | 3 | no |

206 auto-fixable, 23 manual. The auto-fix pass plus a focused review of
the manual 23 is a single session. Note: userMemories carry "238" as
the count; current is 229, so some have been fixed since the count was
recorded.

**Effort:** 1–2 sessions. Auto-fix + manual review pass + per-commit
validation. Bulk-mechanical, low risk, validated at every commit.

**Why now:** "if you've got time to lean, you've got time to clean."
Pure mechanics. Cannot break anything if validated per-commit.

#### H3. F-series finding memo amendment

`OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md` is the original
triage memo for F1–F7. It has not been amended to reflect that all
seven sub-findings (and Findings B/C/D/E spawned after) are now
closed. Per multiple recent memos, "F7 § finding memo amendment"
carries 5+ accumulated bullets.

**Effort:** ~30 min. Pure documentation. Add an addendum log to the
triage memo with the closure timeline.

**Why now:** documentation completeness for future session-start
context loading. Without this amendment, anyone reading the original
F-series triage will think it is still open.

#### H4. `scripts/_status.sh` missing — `scripts/recap` sources it

Verified at HEAD: `scripts/recap` line 5 has `source "$SCRIPT_DIR/_status.sh"`,
file does not exist. Two options per the Operational Plan §9.1: either
restore from git history or remove the source line from the recap
entrypoint.

**Effort:** ~15 min. Single-commit decision-and-act.

**Why now:** the No-such-file line in `prove_ci.sh` output blocks the
final "completely clean" state.

#### H5. Hygiene bundle 9404659 push (items 1, 3, 5)

Per Operational Plan §9.1 and recent memos: locally on commissioner
machine, not pushed. Item 1 includes restoring
`gate_contract_linkage_v1.sh` (the second No-such-file line in
`prove_ci.sh`). Item 4 was subsumed by `70e4003`.

**UNVERIFIABLE FROM FRESH CLONE.** The unpushed work lives on the
canonical commissioner machine. Verifying status requires checking
that machine.

**Effort:** ~10 min once a decision is made on push-as-is vs rebase.

#### H6. Smaller deferred items

These are tracked but each has prior intent-research that should
happen first:

- `d['raw_mfl']` write at `extract_recap_facts_v1.py` (verified at
  line 187 in the actual file: `d["raw_mfl"] = raw`). Per S10 leak
  closure, the `raw_mfl` fallback was retained for pre-promotion
  events. The deferred item is whether this write should remain or
  be removed now. Intent-research required before action.
- Item 4b re-scope (nickname override layer). Pre-existing scope-
  decision deferred from 2026-04-20 nickname work.
- `scripts/diagnose_season_readiness.py:203` latent caller. Flagged
  in a Phase 1 commit message; never picked up.

**Effort:** ~30 min each, but the intent-research question dominates.

### Engine work (genuine new functionality)

#### E1. Verifier check category — player-franchise-week attribution

From `OBSERVATIONS_2026_04_15_STREAK_D12_PROSE_PASS.md` Finding 4: a
class of misattribution where the model produces "Watson scored 23
for KP" and the verifier doesn't catch it because no check covers
per-player-per-week-per-franchise score reconciliation. The memo
explicitly recommends a new verifier check category.

**Shape:** parallel to V1's SCORE check, but per-named-player. Every
named player score in prose is reconciled against the canonical
`WEEKLY_PLAYER_SCORE` row for that player + week + franchise.

**Effort:** ~1 session for V1, regression suite, integration into
lifecycle. Doesn't violate the freeze (same pattern as V1/V2).

#### E2. Verifier check category — temporal claims

From the same memo, Finding 5: "first since X" / "Nth straight Y"
patterns the model produces frequently and gets wrong without canonical
data behind them. Same recommended-shape as E1: ordinal/temporal claims
reconciled against canonical event history.

**Effort:** ~1 session. Could potentially batch with E1.

**Caveat on E1/E2:** the verifier's existing 35/35 weeks clean baseline
means new check categories will, by definition, expose previously-
shipped recaps as containing claims the new check would have caught.
This is fine — the V2 pass that re-validated 2024/2025 already
established the protocol. Re-validation against new checks is part of
shipping new checks.

#### E3. Rivalry Chronicle v1 first composition (Phase F)

The Rivalry Chronicle infrastructure exists (contract card, prove
script, scaffolding) but no first composition has been produced. The
Operational Plan lists this as Phase F.

**Effort:** uncertain — likely 2–4 sessions for first composition,
review, approval. This is content production, not infrastructure
build.

**Caveat:** premature while reception data on the first artifact class
(weekly recap) is still pending. Voice signal from W7 reception could
materially change how a Rivalry Chronicle gets composed. Operational
Plan suggests Phase B (reception accumulation) precedes Phase F.

### Operational work (post-MVP track, depends on reception)

#### O1. Track C — voice iteration tooling

Premature without reception data. Defer until after at least 2–3 weeks
of distributions provide observation accumulation.

#### O2. Track D — operational cadence / scheduler

Documented routine + a "week-ready" status command. Could be done now;
benefits more after at least one cycle of weekly distribution flow has
been observed end-to-end.

**Effort:** 3–5 sessions per the Operational Plan §5.3.

#### O3. Track E — member onboarding contract card

Right moment when a new league member joins; not urgent now.
Operational Plan promotes this to Tier 2 contract card before Phase C.

**Effort:** 2 sessions plus member-facing outreach.

### Bookmarked from prior recent observation memos

These came up in recent sessions, were noted, and have not been picked
up. Not "next priority" but tracked.

#### B1. W7 v25 degenerate render investigation

From `OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` Finding
F1: W7 v25 has length 2572 but the shareable narrative is just the
header line with no body. Either a facts-only fallback path that
produced an effectively-empty narrative, or a creative-layer/verifier
gap that allowed an empty render to persist as DRAFT. The distribution
gate caught it (defense-in-depth worked) but the upstream cause is
unresolved.

**Effort:** half a session for investigation. Naturally pairs with E1
or E2 (verifier work).

#### B2. Runbook DB-path placeholder fix

From the same memo, Finding F2: `docs/runbooks/distribution_v1.md`
shows `data/squadvault.db` in the example invocation; canonical DB is
`.local_squadvault.sqlite` at repo root. ~5 min doc fix.

#### B3. Stale sibling clone cleanup

From the same memo, Finding F3:
`~/projects/squadvault-ingest/.local_squadvault.sqlite` is corrupt;
canonical clone is `~/projects/squadvault-ingest-fresh/`. Local
filesystem cleanup. Does not require a session.

#### B4. Export-assemblies env triage

From multiple memos: 3× "Voice variant rendering retired" warnings
emit from `recap_export_narrative_assemblies_approved.py` due to
environmental setup. ~15 min standalone triage. Distinct scope per its
session brief.

## Recommended next-pickup ordering

Given:

- Reception window for W7 is open (day 0 of 7).
- Track A and Track B are both at "shipped, awaiting reception."
- Engine work (E1/E2) doesn't depend on reception data.
- Hygiene work is unambiguously safe.

**Strong recommendations, in order:**

1. **H1 — Finding B mechanism closure (`set -euo pipefail` to
   `prove_ci.sh`).** 30 minutes. Caps a multi-session workstream that
   has been waiting on this exact one-liner since 2026-04-27. Highest
   leverage per minute.

2. **H3 — F-series finding memo amendment.** 30 minutes. Pure
   documentation. Closing the loop on the workstream H1 caps. After
   this and H1, the prove_ci.sh story is truly finished.

3. **H2 — Tests/ ruff cleanup.** 1–2 sessions. Pure mechanics, can run
   in parallel with the reception window. The auto-fix pass closes
   206 of 229 errors immediately; the manual 23 is a focused review.

4. **H4 — `_status.sh` decision** (restore vs remove the recap source
   line). 15 minutes.

5. After hygiene closes, **E1 / E2 (verifier check categories)** as
   genuine engine work that addresses documented fabrication paths.

**Defer:**

- E3 (Rivalry Chronicle composition) — until reception accumulation
  per Phase B.
- O1/O2/O3 (Tracks C/D/E) — operational; see Operational Plan
  sequencing.
- H5 (hygiene bundle 9404659) — until canonical-machine state can be
  verified, or until commissioner has time to push.

## What this re-grounding pass does NOT do

- Does not modify userMemories beyond the one edit added today
  (player trend detectors complete). Other priority drift in
  userMemories will eventually be corrected by automatic regeneration
  from chat history.
- Does not pick a track for the next session — that's the
  commissioner's call from this list.
- Does not verify items requiring local-only state (unpushed commits,
  local DB contents). Those are flagged UNVERIFIABLE-FROM-FRESH-CLONE
  where applicable.
- Does not examine the deeper engine surface for items not surfaced in
  recent memos. The list is "what was tracked"; there may be surfaces
  not surfaced (literally) that this pass misses.

## Cross-references

- `Phase_10_Observation_T1_Verification_and_Trade_Loader_Bug.md` —
  T1 done, trade loader bookmarked (now closed).
- `Phase_10_Observation_NAv2_Verification_Streak_Momentum_and_Trade_Loader.md` —
  trade loader closure at `39c8f1c`.
- `OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md` — original
  F-series triage, now mostly closed.
- `OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md` — Finding B mechanism
  closure unblocked.
- `OBSERVATIONS_2026_04_15_STREAK_D12_PROSE_PASS.md` — Findings 4 and
  5 (sources of E1 and E2).
- `OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — Track A
  shipping, including B1/B2/B3 bookmarks.
- `OBSERVATIONS_2026_04_28_TRACK_B_RECEPTION_CAPTURE_SHIPPED.md` —
  Track B shipping.
- `SquadVault_Operational_Plan_v1_1.md` — Tracks A–E and Phase F
  definitions.
