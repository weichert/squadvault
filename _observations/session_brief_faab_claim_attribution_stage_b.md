Session Brief — FAAB_CLAIM Attribution, Stage B (Prose Capture)
Date authored: 2026-07-02 (DECIDE session; sequencing "Stage B now, fix scoping after" ratified 2026-07-02)
Session type: EXECUTE (Claude Code), two founder gates (⛔ Gate 1: pre-registration; ⛔ Gate 2: memo approval)
Repo: engine (weichert/squadvault) — confirm identity with test -f scripts/recap_artifact_regenerate.py
Plan reference: follow-on to Stage A (memo + brief at squash 9571885); D-V staged design; D-W diagnosis-only discipline carries over
Why now: Stage A left 9 of 11 cells H3 (indeterminate without prose). Stage B resolves them, so fix scoping can precede the 07-18 runbook trigger with room for fix + re-measurement before Draft Weekend (08-15).

Paste-ready kickoff prompt

You are an EXECUTE session for SquadVault FAAB_CLAIM Attribution, Stage B: prose capture on the 9 H3 cells. Read _observations/session_brief_faab_claim_attribution_stage_b.md in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, git log -1 to verify HEAD, repo identity via test -f scripts/recap_artifact_regenerate.py. Two-lane discipline: you execute; the founder adjudicates at the two ⛔ gates. Hard rules: no pinned-cell generation until the pre-registration block is founder-ratified (Gate 1); the single smoke generation on a throwaway cell is permitted before Gate 1. This session is still diagnosis-only (D-W): no edits to verifier, prompts, Tier-2 policy, data layer, or any source file. All generation runs against a scratch DB copy; prod is hashed at start and end and must be unchanged. Nothing is published. The Stage A memo and the A7 baseline are frozen history — read, never amend.


1. Objective
For each of the 9 inherited H3 cells, capture the FAAB-implicated prose and verifier internals sufficient to assign a terminal classification:

H1p — model invention: the model attaches a dollar amount to a player with no WAIVER_BID_AWARDED record (e.g., an amount-less TRANSACTION_FREE_AGENT add), or invents an amount contradicting the record by >$1.
H2p — proximity misbinding: the model's FAAB sentence is factually correct, but the verifier's nearest-player-within-100-chars binder attaches the dollar to the wrong player, producing a false failure.
H3p — other: anything not cleanly either; described verbatim, not forced into a bucket.

This is attribution, not measurement: the readout is a per-cell mechanism classification, not a rate. Stage B results are not comparable to the A7 baseline and the memo must say so — different model invocations produce different prose; a cell may even pass here. A cell that passes verification on all attempts in Stage B is recorded as NO_FAILURE_REPRODUCED — a legitimate terminal class, not a defect of the run.
2. Pre-registered capture fields (per FAAB_CLAIM failure event)
Frozen at Gate 1, from the Stage A memo's capture list:

The verbatim FAAB-implicated sentence(s) from the rejected draft.
The claimed dollar amount and the player name the model attached it to.
The verifier's best_name binding for that claim (which player the binder resolved, and the character distance).
Whether that player — and any player within the binder window — has a real WAIVER_BID_AWARDED record for the season, with the canonical amount.
The pickup event type(s) surfaced for the named player in that cell's bullets (WAIVER_BID_AWARDED / TRANSACTION_FREE_AGENT / none).

Plus per-cell run metadata: attempt count, per-attempt FAAB_CLAIM failure yes/no, final outcome.
3. Non-negotiable constraints

Cell list inherited, not drawn. The 9 H3 cells exactly as listed in the Stage A memo — extract verbatim from the memo; the memo governs over any other rendering of the list. n=9, no sampling: the population is the sample. No substitutions; a cell that cannot run is INELIGIBLE_POST_PIN.
Scratch DB. Copy prod to scratch; record prod's hash at start and end (must match). All generation, lifecycle writes, and prompt_audit rows land in scratch only.
Production configuration, as-is. Model id read from creative_layer_v1.py at HEAD (expected claude-sonnet-4-5-20250929 — verify, don't assume); no prompt/verifier/policy edits; retry loop as shipped. Voice-profile state recorded.
Prose retention. Unlike A7, the captured fields are the deliverable. All five fields per failure event are transcribed into the memo itself before the scratch DB is deleted — the A7 lesson (evidence deleted with scratch) is not repeated. Scratch is deleted only after Gate 2 approval confirms the memo captures everything.
ANTHROPIC_API_KEY via the set -a; source .env.local; set +a pattern; smoke generation on one throwaway cell (not among the 9, excluded and recorded) before Gate 1 to prove no facts-only key degradation.
Nothing published; no source edits; repo diff at end is the memo (± STATE line per charter §3.11, separate commit per the established pattern).

4. Procedure
Step 0 — Ritual. Fresh clone, HEAD recorded, identity check, standard trio green.
Step 1 — Scratch + smoke. Copy DB, record prod hash, smoke one throwaway cell, confirm real generation + verifier engagement + prompt_audit capture.
Step 2 — Pre-registration block (draft). HEAD hash; prod-DB hash; model id (read from config); voice-profile state; retry policy; the 9-cell list extracted verbatim from the Stage A memo; the 5 capture fields; the three terminal classes plus NO_FAILURE_REPRODUCED and INELIGIBLE_POST_PIN; the classification decision rule per field-pattern, written before any generation.
⛔ Gate 1 — Founder ratifies. Block frozen after ratification.
Step 3 — Run. Generate the 9 cells sequentially against scratch. For every attempt that fails FAAB_CLAIM, capture all 5 fields immediately (from the draft text and the verifier's failure detail / prompt_audit rows). Infrastructure retries are noted and don't count as verification attempts. No mid-run intervention.
Step 4 — Classification. Apply the pre-registered decision rule per cell. A cell with multiple FAAB failure events across attempts is classified by mechanism per event; the cell's terminal class is the dominant mechanism, with mixed cells labeled explicitly.
Step 5 — Memo. _observations/OBSERVATIONS_2026_07_XX_FAAB_CLAIM_ATTRIBUTION_STAGE_B.md: frozen block, smoke record, per-cell capture tables (all five fields, verbatim prose quoted), classification with per-cell evidence, the non-comparability statement (§1), and a closing that names the responsible layer(s) — assembly, verifier binder, or both — with no fix design (D-W). Exploratory observations in a labeled appendix.
⛔ Gate 2 — Founder approves; commit (memo commit + STATE commit per pattern; founder-written messages via /tmp/msg.txt, ASCII subjects, no Co-Authored-By; one PR, gh pr merge --squash via CLI). Scratch deleted only after the squash lands on main.
5. Acceptance criteria

Frozen pre-registration block predates all pinned-cell generation.
All 9 cells terminal: H1p / H2p / H3p / NO_FAILURE_REPRODUCED / INELIGIBLE_POST_PIN — none dropped.
Every classification traceable to captured fields quoted in the memo; prose survives scratch deletion.
Prod hash unchanged start-to-end; nothing published; repo diff is memo (+ STATE line).
Standard trio green at session end.

6. Known hazards

Directory confusion — identity test first.
Dead-key facts-only degradation — the smoke exists for this.
Capture-before-delete is the whole point — do not let cleanup habits from A7 delete evidence before Gate 2.
The binder's failure detail may not natively expose best_name/distance in output; if so, reproduce the binding deterministically from the rejected prose using the verifier's own logic (read-only), and say in the memo that field 3 was reconstructed, not logged.
Non-comparability discipline: no sentence in the memo may read Stage B's pass/fail pattern as a rate update to the baseline.

7. Out of scope
Any fix (assembly, verifier, prompt, data) · re-running A7 or amending Stage A · the H1 fix for 2019/2020 (already attributed; scoped after Stage B per ratified sequencing) · enum/doc updates (Unit A4) · additional cells beyond the 9.
