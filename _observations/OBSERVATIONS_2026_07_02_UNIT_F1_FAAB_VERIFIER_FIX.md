# Observation - 2026-07-02 - Unit F1: FAAB_CLAIM Verifier Vocabulary + Binder-Crossover Fix

**Session type:** EXECUTE (Claude Code, Opus 4.8). Two founder gates (Gate 1 test plan +
design note; Gate 2 diff + memo + merge). Brief:
`_observations/session_brief_unit_f1_faab_verifier_fix.md` (landed squash `b0b675b`).
Follow-on to FAAB_CLAIM Attribution Stage B (memo `..._FAAB_CLAIM_ATTRIBUTION_STAGE_B.md`,
squash `7f436bd`).

**Status:** Implemented; presented at Gate 2. Nothing published (verifier-only change; no
prompt/assembly/Tier-2/data-layer edits; no generation).

---

## 0. Ritual / provenance

- **HEAD at start:** `b0b675b` (the brief commit; verified `git log -1`).
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Canonical DB (read-only):** `.local_squadvault.sqlite`, hash `effb00e54fce5c38...`
  **unchanged** start-to-end (identical to the Stage B scratch source). All reverify ran
  against a scratch copy in the session scratchpad; prod/local corpus never written.
- **Standard trio (post-implementation):** `ruff check src/squadvault/` clean; mypy clean
  (160 source files); pytest **2393 passed, 2 skipped** (2380 pre-existing + 13 new F1).

## 1. Gate history

- **Gate 1 (test plan + design note) RATIFIED 2026-07-02** with three ratification-time
  additions folded in (this memo discharges 2 and 3; see sections 3, 6, 7):
  1. read-only attribution probe for the `$98.15` franchise (section 3);
  2. this Stage B correction section (section 4, append-only; the Stage B memo is NOT amended);
  3. ruff CI-scope confirmation (section 7).
  Frozen at ratification: 13 tests with fixed expected outcomes; crossover conditioned on the
  amount-owner named in-window; defense map uniqueness-guarded (ambiguous cities dropped);
  franchise-total shape dropped with `michele_98` as the no-accidental-rescue guard;
  reconstructed-decoy fidelity caveat recorded (section 6).

## 2. Design as implemented

The FAAB_CLAIM check previously force-bound every FAAB dollar to the nearest player name
within 100 chars and failed if that player lacked a matching `WAIVER_BID_AWARDED` (WBA)
record. Stage B proved this produced false positives on correct non-player-scoped or
adjacent claims. The fix rests on a single invariant and two shapes:

- **D-Z invariant.** A claim passes only when a real canonical WBA for an entity *actually
  referenced within the +/-100-char window* matches the amount within +/-$1. Proximity alone
  never validates.
- **Shape A - crossover rebind (F1b).** Before failing, if any player named in-window has a
  WBA matching the amount, the claim binds to that player (not the merely-nearest name). The
  amount-owner must be *named in the window*: an explicit false attribution to a WBA-less
  player, whose amount belongs to an unnamed player, finds no in-window owner and still fails.
- **Shape B - defense-entity resolution (F1a defense + team-name).** Team defenses are
  rosterable `player_directory` rows (position `Def`, "`<Nickname>, <City>`"). A
  uniqueness-guarded token->pid map (nickname always; city only with a defense-signal word in
  the window) resolves references the per-player binder cannot see; the claim is validated
  against that defense's own WBA (match -> pass; no matching record -> fail). Ambiguous cities
  (Los Angeles = Chargers + Rams; New York = Jets + Giants) are dropped. A proper-noun guard
  (uppercase initial in the original text) keeps nickname-words ("Rams", "Bills", "Jets") from
  matching lowercase prose. Defense WBAs are already in the loaded bid map (defenses carry
  player ids).
- **Franchise-total (F1a-i) - DROPPED** per founder ruling (section 3). No franchise-total
  validation is built; `michele_98` guards that dropping it does not accidentally rescue.

**Surface.** Entirely inside `verify_faab_claims` plus two new helpers
(`_load_faab_defense_tokens`, `_faab_defense_token_index`) and one signal pattern, all in
`recap_verifier_v1.py`. No new parameters; **no dispatcher, Tier-2 policy, assembly, prompt,
enum, or data-layer change.** Both shapes are season-scoped like the existing check.

## 3. Attribution probe (Gate 1 addition 1; read-only)

Season-scoped franchise/owner resolution, 2024:

- The `~$98.15` 2024 FAAB total belongs to **franchise 0005, "Weichert's Warmongers"**
  (owner field empty).
- **"Michele" = franchise 0009, "Italian Cavallini", whose 2024 FAAB total is `$99.99`.**
- Through week 4 (the recap's window), 0005 had spent `~$31.05`; the league-wide max through
  wk4 was `$41.23` (0009). No franchise is near `$98` until season end. Assembly renders FAAB
  windowed to the recap week (`derive_faab_spending(..., through_occurred_at=window_end)`,
  `weekly_recap_lifecycle.py:1030`).

**Finding:** the wk4 "$98" claim is a **double fabrication** - false by temporal window
(real through-wk4 `~$31`, claimed `$98 through four weeks - most in the league`) **and** by
franchise attribution (0005's season total pinned on 0009/Michele). Note `$98` is within
+/-$1 of 0005's `$98.15` but off by `~$2` from Michele's own `$99.99`, so even a full-season
franchise-total check keyed to the named franchise would fail it.

## 4. Stage B correction (append-only; the Stage B memo is NOT amended)

The Stage B memo (`..._FAAB_CLAIM_ATTRIBUTION_STAGE_B.md`) classified the 2024 wk4 "$98"
event as **H3p** - "franchise-total scope, a true statement misbound to a player" - a
verifier false positive. That classification rested on an appendix probe of **full-season**
franchise totals (matching `$98` to 0005's `$98.15`) and did not check the through-week-4
figure or the named franchise.

On this unit's evidence (section 3), the "$98" event is **reclassified as a fabrication**
(temporal, and attributional). Consequences:

- **Corrected Stage B event tally: 7 of 9 false positives and 2 fabrications**
  (was 8 false positives / 1 fabrication). The Pitts `$39` H1p is unchanged; the wk4 "$98"
  H3p moves from false-positive to fabrication.
- The verifier's rejection of the "$98" event was **correct for the wrong reason**: it
  fired on per-player misbinding (binding `$98` to Dontayvion Wicks), while the true reason
  for rejection - temporal and franchise falsity - was invisible to Stage B's season-total
  check. Unit F1 leaves the event correctly failing; it does not (and per the dropped shape,
  cannot) claim to detect the temporal/attribution falsity directly.

The STATE.md Stage B bullet's "8/9" figure is corrected to "7/9" in the same commit series
(one line; founder-worded at Gate 2).

## 5. Fixture + adversarial results

All 13 Unit F1 tests green post-fix; each was verified failing-as-expected against `b0b675b`
before implementation (Gate 1). Every rescue fixture reproduces the Stage B memo's field-F3
misbinding exactly.

| Test | Encodes | Post-fix |
|------|---------|----------|
| `cleveland_defense_5_passes` | $5 -> Cleveland DEF `0507` $5.01 | PASS |
| `chicago_defense_zero_passes` | $0 -> Bears DEF `0521` $0.01 | PASS |
| `chargers_defense_2_or_3_passes` | $2/$3 -> Chargers DEF `0514` $2.55 | PASS |
| `jennings_35_crossover_passes` | $35 -> Jennings $35.01 (named) | PASS |
| `darnold_9_crossover_passes` | $9 -> Darnold $9.11 (named) | PASS |
| `bigsby_4_crossover_passes` | $4 -> Bigsby $4.42 (named) | PASS |
| `pitts_39_invention_still_fails` | $39 Pitts; Fant $38.07 not in-window | FAIL (kept) |
| `michele_98_temporal_fabrication_still_fails` | $98 fails; $52 (Wicks $52.78) does not | FAIL (kept) |
| `near_miss_invention_fails` (adv 1) | $38 vs $35.01 (>$1) | FAIL (kept) |
| `explicit_false_attribution_fails` (adv 2) | $35 to WBA-less Jennings, owner unnamed | FAIL (kept) |
| `invented_defense_fails` (adv 4) | $50 Raiders DEF, no record | FAIL (new coverage) |
| `a7_smoke_pair_fails` (adv 5) | $11 Burrow / $5 Cousins, no WBA | FAIL (kept) |
| `compound_defense_ok_invention_fails` (adv 6) | $0 Bears passes, $39 Pitts fails | 1 FAIL |

Adversarial 3 (invented franchise total) is **N/A** - the franchise-total shape is dropped,
so there is no franchise-total validation to over-trust; `michele_98` is the guard that
dropping it does not accidentally rescue.

## 6. Fidelity caveat (recorded per hazard section 6)

- **Reconstructed decoys.** The three crossover fixtures (Jennings / Darnold / Bigsby) use
  the memo's FAAB phrasing but the memo captured only the FAAB sentence, not the full
  +/-100-char draft window that held the nearer WBA-less misbinder named in field F3 (Breece
  Hall / Jaylen Waddle / Jayden Daniels). Those decoy clauses are **reconstructed** to
  reproduce the documented F3 nearest-name binding; the mechanism (owner in-window with a
  real WBA, decoy nearer without one) is faithful. The Stage B scratch prose was not retained.
- **Darnold 1-char correction (disclosed, with ratification reasoning).** The memo's
  byte-exact sentence names Sam Darnold as the amount-owner of the `$9` claim ($9.11), and
  Stage B classified the event **H2p** - i.e. Darnold is the in-window, rescuable owner. In
  the Gate-1 fixture the **reconstructed decoy padding** placed "Sam Darnold" 101 chars from
  `$9` - 1 char beyond the frozen +/-100 crossover window - which is internally inconsistent
  with **both** the frozen +/-100 spec **and** the ratified H2p classification (an owner the
  design cannot reach cannot be the H2p rescuable owner). The repair tightens the
  reconstructed context so Darnold sits in-window (37) with Waddle nearer (24). It corrects
  the **reconstruction**, not a ratified outcome: the fixture's ratified expected outcome
  (pass) is unchanged, and the byte-exact FAAB phrasing and F2/F3 mechanism are preserved.

## 7. Category-breakdown non-regression (merge gate)

Method: prod/local corpus copied to a scratch DB (hash identical, `effb00e5...`); the current
verifier (`f1fix`) and the baseline verifier (`baseb0b675b`, source stashed to `b0b675b`)
each reverified all 365 `prompt_audit` drafts for league 70985 on the scratch copy; per-
category HARD-failure counts compared.

**Reverify dedup (recorded).** The first baseline reverify **timed out mid-write**, leaving
partial rows under the `baseb0b675b` tag; a second full run appended a complete pass, so that
tag held duplicate rows. Because both the partial and the full run used identical stashed
baseline (`b0b675b`) code, the duplicates were exact and were **deduped one-per-draft** (keep
`MIN(id)` per `prompt_audit_id`). Post-dedup **both tags held exactly 365 rows**, and the
category comparison below was **run clean** against those deduped rows.

Result - **only FAAB_CLAIM moves, downward; every other category unchanged:**

```
FAAB_CLAIM              base=123  fix=89   delta=-34
CHAMPIONSHIP_CLAIM       28        28        0
DRAFT_AUCTION_DOLLAR     13        13        0
PLAYER_AVG_CLAIM          4         4        0
PLAYER_FRANCHISE          9         9        0
PLAYER_SCORE              2         2        0
PLAYER_STREAK_CLAIM      16        16        0
RECORD_CLAIM_ANCHORING   19        19        0
SCORE_VERBATIM          579       579        0
SEASON_RECORD_CLAIM      20        20        0
SERIES                   93        93        0
STREAK                   99        99        0
SUPERLATIVE              73        73        0
```

No new category surface. The FAAB drop is net of both false positives removed (crossover +
defense rescues) and invented defenses newly caught (adv 4).

**Ruff CI scope (Gate 1 addition 3):** CI runs `ruff check src/squadvault/` (`ci.yml:52`),
clean at HEAD. The 6 pre-existing ruff errors this session surfaced live in `Tests/`
(line 12 import + lines 5982-6237) - **outside** the CI ruff scope; the trio-green criterion
refers to the CI invocation.

## 8. Diff span and scope

- `src/squadvault/core/recaps/verification/recap_verifier_v1.py` ~L4478-4700 (the
  `_load_faab_bids` neighborhood through `verify_faab_claims`); +2 helpers, +1 pattern.
- `Tests/test_recap_verifier_v1.py` +378 (three F1 test classes).
- **Tier-2 policy and assembly untouched** (confirmed: no diff hunk outside the FAAB region;
  `FAAB_CLAIM` remains a Tier-2 no-retry category unchanged).

## 9. Not measured (D-Y)

This memo does **not** claim a measured fix effect on the fresh-generation failure rate. The
category delta above is a reverify-corpus non-regression check, not a re-measurement. Per
D-Y, re-measurement is a separate pre-registered unit.
