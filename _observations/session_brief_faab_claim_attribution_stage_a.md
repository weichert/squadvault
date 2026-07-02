Session Brief — FAAB_CLAIM Attribution, Stage A (Deterministic)
Date authored: 2026-07-02 (DECIDE session; D-U/D-V/D-W ratified 2026-07-02)
Session type: EXECUTE (Claude Code), one founder gate (⛔ Gate 1: memo approval)
Repo: engine (weichert/squadvault) — confirm identity with test -f scripts/recap_artifact_regenerate.py
Plan reference: follow-on to Unit A7 baseline (memo committed at squash 1948de4); Phase-2 failure-rate-attribution precedent
Why now: FAAB_CLAIM drove 11 of 16 facts-only outcomes in the pre-season baseline (44.4% facts-only overall). Attribution must complete with room for a possible fix unit and re-measurement before Week 1 (~09-08), with Draft Weekend (08-15) consuming mid-August.

Paste-ready kickoff prompt

You are an EXECUTE session for SquadVault FAAB_CLAIM Attribution, Stage A. Read _observations/session_brief_faab_claim_attribution_stage_a.md in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, git log -1 to verify HEAD, repo identity via test -f scripts/recap_artifact_regenerate.py. Two-lane discipline: you execute; the founder adjudicates at Gate 1. Hard rules: this session is diagnosis-only (D-W) — no edits to the verifier, prompts, Tier-2 policy, data layer, or any source file; the production DB is opened read-only and its hash is recorded at session start and re-verified at session end; no generation API calls of any kind. The A7 baseline memo is frozen history — read it, never amend it. Silence over speculation: where evidence is absent, the memo says so.


1. Objective
Determine, from code and data alone, why FAAB_CLAIM dominates verification failure, by structurally separating two pre-declared hypotheses:

H1 — Data starvation: FAAB facts are absent, incomplete, or not surfaced into the prompt assembly for the implicated cells, so the model invents FAAB claims (the known invent-when-starved pattern).
H2 — Verifier over-strictness: FAAB data reaches the prompt and the model's claims are substantively correct, but the FAAB_CLAIM check rejects valid phrasings (e.g., rendering/format mismatch against canonical strings).

A third outcome is permitted: H3 — indeterminate without prose, in which case the memo states exactly what Stage B must capture to resolve it. Stage A does not guess.
2. Non-negotiable constraints

Read-only. shasum the prod DB at session start; open connections read-only (file:...?mode=ro URI or equivalent); re-verify the hash at session end. Both hashes go in the memo.
No generation. Zero API calls. ANTHROPIC_API_KEY should not be needed; do not source it.
No source edits. Repo diff at session end is the memo file only (plus a STATE.md discharge line if the charter's §3.11 requires one — same two-commit series pattern as A7 if so).
Cell list is inherited, not drawn. The implicated cells are the 11 FAAB_CLAIM Tier-2 short-circuit cells recorded in the A7 memo (_observations/OBSERVATIONS_..._UNIT_1_4_FRESH_GENERATION_BASELINE.md). Extract them from the memo verbatim; do not re-derive or substitute. Note: the baseline scratch DB was deleted per Gate 2 — per-attempt prose does not exist; work only from what the memo, code, and prod data provide.
Enum reality. The verifier emits 19 categories, not the 14 in older docs. Read the enum from the verifier source at HEAD; if FAAB_CLAIM's semantics interact with adjacent categories, describe from code, not from stale docs.
Census-first. Every data claim in the memo cites the SQL probe and its verbatim result.

3. Procedure
Step 0 — Ritual. Fresh clone, HEAD verified and recorded, identity check, install, standard trio green. Prod DB start-hash recorded.
Step 1 — Code reading (verifier side). Locate and document: the FAAB_CLAIM check's exact matching logic in recap_verifier_v1.py (what constitutes a claim; what it compares against; exact-string vs. normalized comparison); the Tier-2 short-circuit policy for FAAB_CLAIM (why it short-circuits rather than retrying — quote the code path). Record file paths and line references at HEAD.
Step 2 — Code reading (assembly side). Trace how FAAB facts flow into prompt assembly: which tables/helpers supply FAAB data, whether a canonical pre-rendered string exists (per the four-step playbook; check against the FAAB Outcome Insight contract card), and under what conditions FAAB content is included, omitted, or partially surfaced for a weekly recap cell.
Step 3 — Data probes. For each of the 11 inherited cells: does complete FAAB data exist in prod at that (season, week)? Would the assembly path (per Step 2's reading) have surfaced it into the prompt context? Produce a per-cell table: (season, week) | FAAB data present? | reaches prompt per code path? | notes. Save all probe SQL verbatim.
Step 4 — Classification. Assign each cell H1 / H2 / H3 with the specific evidence line. Pre-declared decision rule: data absent or not surfaced → H1; data present and surfaced, and the verifier's comparison is demonstrably stricter than the canonical form the assembly provides → H2; data present and surfaced but the failure mechanism cannot be established without the rejected prose → H3.
Step 5 — Memo. _observations/OBSERVATIONS_2026_07_XX_FAAB_CLAIM_ATTRIBUTION_STAGE_A.md: start/end DB hashes, HEAD, code-reading findings with line refs, per-cell table, classification counts, and a closing section that is strictly one of: (a) attribution established — a fix unit can be scoped (no fix design in this memo beyond naming the responsible layer), or (b) Stage B required — with the exact capture list Stage B needs. Exploratory observations go in a labeled non-load-bearing appendix.
⛔ Gate 1 — Founder approves the memo; commit (doc-only, _observations/, founder-written message via /tmp/msg.txt, ASCII subject, no Co-Authored-By trailer, gh pr merge --squash via CLI).
4. Acceptance criteria

Prod DB start/end hashes identical, recorded in the memo.
All 11 inherited cells classified H1/H2/H3 with cited evidence; no cell silently dropped.
Every data claim traceable to included SQL + result; every code claim to file:line at recorded HEAD.
Repo diff: memo only (± the STATE discharge commit if charter-required).
Zero API calls; standard trio green at session end.

5. Known hazards

H3 directory confusion — identity test first.
The A7 memo is the sole source for the cell list; a grep-style misread of it is how the last false carry-forward happened — quote the cells from the memo's R2/short-circuit section explicitly.
Do not conflate "FAAB data exists in DB" with "FAAB data reaches the prompt" — those are Steps 3's two separate columns for a reason.
Diagnosis-only pressure: if the code reading makes a fix look obvious, the memo may name the layer, nothing more (D-W).

6. Out of scope
Any fix (verifier, prompt, assembly, data) · Stage B execution · re-running or amending the baseline · enum documentation updates (Unit A4) · Tier-2 policy discussion beyond describing the code as it stands.
