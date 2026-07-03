# Session Brief — Unit F2: FAAB Starvation Suppression (Zero-WBA Seasons)

**Date authored:** 2026-07-02 (DECIDE session; D-X disposition 4, ratified 2026-07-02)
**Session type:** EXECUTE (Claude Code), two founder gates (⛔ Gate 1: test plan + design note; ⛔ Gate 2: diff review + merge)
**Repo:** engine (`weichert/squadvault`) — confirm identity with `test -f scripts/recap_artifact_regenerate.py`
**Plan reference:** Stage A attribution (H1, proven: 2019/2020 have zero season WAIVER_BID_AWARDED events); D-X disposition 4; Unit F1 landed at `6778101`
**Scope in one line:** when a season has no FAAB data, the prompt must not invite FAAB talk — suppress FAAB angles and writer-room FAAB context for zero-WBA seasons; silence over speculation, implemented.

---

## Paste-ready kickoff prompt

> You are an EXECUTE session for SquadVault Unit F2: FAAB starvation suppression. Read `_observations/session_brief_unit_f2_faab_starvation_suppression.md` in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, `git log -1` to verify HEAD, repo identity via `test -f scripts/recap_artifact_regenerate.py`. Two-lane discipline: you execute; the founder adjudicates at the two ⛔ gates. **Hard rules: this unit modifies ONLY the assembly-side FAAB context gating (angle detectors and writer-room FAAB derivations as wired into weekly prompt assembly) and its tests — no verifier, Tier-2, prompt-template, or data-layer changes; no generation API calls; prod DB read-only, hashed at start and end. Tests are written and founder-ratified BEFORE implementation (Gate 1). Suppression must be keyed to the data (season WBA count = 0), never to hardcoded season numbers.** Nothing is published.

---

## 1. Objective

Stage A proved the H1 mechanism: for seasons with zero WAIVER_BID_AWARDED events (2019, 2020 in the current corpus), the weekly prompt still receives FAAB narrative angles (detectors 17/18) and/or writer-room FAAB context (`derive_faab_spending` / `derive_faab_acquisitions` / `derive_faab_roi` wiring), inviting the model to produce FAAB sentences for which no fact exists — pure invent-when-starved. The fix: when the season's WBA count is zero, no FAAB angle and no writer-room FAAB context enters the weekly prompt assembly. The model cannot invent dollars for a topic it was never handed.

Boundaries:

- `TRANSACTION_FREE_AGENT` bullets are untouched. Free-agent adds are real canonical events and remain surfaced (amount-less, as designed). This unit gates FAAB context, not transaction facts.
- Non-zero-WBA seasons are behaviorally unchanged — byte-identical assembly output for a season with any WBA data.
- Data-keyed, not season-keyed: the gate reads the season's WBA count from canonical data at assembly time. If a future season legitimately has no auction/FAAB data (cf. the 2021 C4 draft-kind precedent), it is protected automatically; if 2019 data were ever back-filled via the Manual Source Adapter, the gate opens without a code change.

## 2. Design constraints

- Single gating point per surface, at the assembly seam. Prefer gating where the detectors/derivations are wired into weekly assembly over adding internal early-returns in each derivation — one visible condition, not five scattered ones. The design note at Gate 1 states the chosen seam with `file:line` references.
- The zero-count probe must be canonical: the same event source the derivations themselves read (`v_canonical_best_events` / WBA per Stage A's reading), season-scoped. No new notion of "FAAB exists" may be invented.
- No prompt-template change: the template must already tolerate absent FAAB context (verify — if the template unconditionally references a FAAB section, that's a finding to surface at Gate 1, not to silently fix).

## 3. Test plan requirements (written at Gate 1, before implementation)

Deterministic, assembly-level, no generation:

1. **Zero-WBA season** (2019 or 2020 fixture): suppression. Weekly assembly output contains no FAAB angle and no writer-room FAAB context. Red now, green post-fix.
2. **Non-zero season** (e.g., 2024 fixture): unchanged. Assembly output for a WBA-bearing season is byte-identical pre/post fix (hash comparison or equivalent). Green now, green post-fix.
3. **Free-agent preservation**: a zero-WBA season week containing `TRANSACTION_FREE_AGENT` events still surfaces those bullets. Green now, green post-fix.
4. **Data-keyed proof**: the gate opens when a WBA row is present for an otherwise-zero season fixture (synthetic fixture DB acceptable) — proving no hardcoded season list.
5. **Boundary**: a season with exactly one WBA event is treated as non-zero (full FAAB context).

## 4. Procedure

**Step 0 — Ritual.** Fresh clone, HEAD recorded (at or past `6778101`), identity check, standard trio green, prod hash recorded.

**Step 1 — Code reading + test plan + design note (no implementation).** Re-verify Stage A's wiring reading at current HEAD (the F1 merge touched only the verifier, but verify, don't assume); write the §3 tests red/green as specified; write the design note (chosen seam, `file:line`, the canonical zero-count probe, and the §2.3 template check result).

**⛔ Gate 1 — Founder ratifies test plan + design note.** Tests freeze: outcomes may not change post-ratification; tests may be added.

**Step 2 — Implement.** Surgical diff at the ratified seam.

**Step 3 — Prove.** Trio green; ratified tests green; prove_ci exit 0 on the clean tree. Category-breakdown reverify is NOT required for this unit (no verifier change), but the memo must state that explicitly rather than silently omit it.

**Step 4 — Memo.** `_observations/OBSERVATIONS_2026_07_XX_UNIT_F2_FAAB_STARVATION_SUPPRESSION.md`: design as implemented, test results, diff span, the template-check result, explicit statements that verifier/Tier-2/templates were untouched and that effect is NOT measured (re-measurement is the separate D-Y unit).

**⛔ Gate 2 — Founder reviews diff + memo; merge.** Commit series per convention (source+tests, memo, STATE line; founder-written messages via `/tmp/msg.txt`, ASCII subjects, no Co-Authored-By), one PR, `gh pr merge --squash` via CLI, verify on fresh main.

## 5. Acceptance criteria

- All five §3 test classes green post-fix; non-zero-season assembly byte-identical; no hardcoded seasons (test 4 proves it).
- Diff confined to the ratified assembly seam + tests; verifier, Tier-2, templates, data layer untouched (diff span stated in memo).
- Trio green; prove_ci exit 0; prod hash unchanged start to end.
- Effect not claimed as measured.

## 6. Known hazards

- Directory confusion — identity test first.
- Season-scoped discipline: the zero-count probe takes the season parameter explicitly (the LEAGUE_HISTORY temporal-scoping lesson applies — no implicit "current corpus" reads).
- The byte-identical test (§3.2) is the guard against accidental behavior change on healthy seasons — if it cannot be made byte-exact, that's a Gate 1 conversation, not a quiet relaxation.
- prove_ci: clean tree + disk space before invoking.

## 7. Out of scope

Verifier changes (F1 is landed and closed) · Tier-2 policy · prompt-template edits · Manual Source Adapter / 2019-2020 back-fill · re-measurement (separate pre-registered unit per D-Y) · surfacing an explicit "no FAAB data" prompt signal (the ratified D-X disposition is suppression, not signaling).
