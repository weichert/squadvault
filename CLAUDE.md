# SquadVault Working Process Charter v1.0

**This file is process law.** It is auto-loaded by Claude Code at session start and MUST be
read before any other action in any session (Claude Code or chat). Sessions follow it
exactly. A session that believes a better process exists proposes a charter amendment to
the founder; it NEVER silently deviates. "I improved the workflow" without an approved
amendment is a process violation, not initiative.

**Authority:** Operational (Tier 4-adjacent). Where this charter conflicts with any
Tier 0-4 canonical document, the canonical document governs. Architecture is frozen.
Facts are immutable and append-only. AI assists; humans approve publication. Silence
over speculation. No analytics, optimization, engagement loops, or prediction - ever.

**Product plan of record:** `docs/SquadVault_Product_Document_of_Record_v2_1.md` (v2.1, in-repo).
**Amendments to this charter:** append-only, dated, founder-approved, logged in section 9.

---

## 1. Tool routing - which medium for which work

| Work | Tool | Model |
|---|---|---|
| Code, tests, gates, migrations, scripts, file edits, commits | **Claude Code** (terminal or VS Code) | Opus 4.8 |
| Constitutional memos, four-memo chains, specs, decision-readiness, protocols, retrospectives, Closure Memo | **Chat** (claude.ai project) | Fable |
| Planning / re-baseline sessions | Chat | Fable (rare - see 2.3) |
| Doc-only repo edits (observation memos, STATE.md, runbooks) | Claude Code | Opus 4.8 |
| Quick questions, mobile, reading the archive | Chat or mobile app | either |

**Claude Code replaces the chat-to-terminal paste pipeline entirely.** The following
chat-era mechanics are OBSOLETE for Claude Code sessions and must not be reintroduced:
base64 round-trip file writers; apply scripts in `~/sv-apply/`; commit-message-via-
python-write_text; heredoc workarounds; glob tricks avoiding literal `.md`; paste-turn
separation. They were compensation for a lossy clipboard channel that no longer exists.

**What SURVIVES unchanged in Claude Code** (these are repo law, not paste law):
- All pre-commit gates (banner, xtrace, repo-root allowlist, docs-Map) and prove_ci.
- Gates and commits remain separate steps - never chained with `&&`.
- prove_ci requires a completely clean tree: commit first, prove on clean tree, push.
- One topic per commit. ASCII in commit messages (`-` not em-dash, `section X` not `§X`).
- Observation memos live in `_observations/`, never repo root (allowlist enforces).
- Doc-only commits skip prove_ci but run the other gates.
- Env re-export each session (`$DB`, `ANTHROPIC_API_KEY` do not persist):
  `set -a; source .env.local; set +a`.
- Repo identity check before acting: `test -f scripts/recap_artifact_regenerate.py`
  confirms the engine repo (both repos can render identical prompts).

**Chat sessions that still touch the terminal** (should now be rare) retain the full
legacy paste discipline recorded in userMemories and prior charters.

## 2. Model routing - Fable vs Opus

**2.1 The one-question test:** does this session DECIDE or EXECUTE?
- DECIDE (output = a memo other sessions will obey) -> Fable, in chat.
- EXECUTE (output = commits against acceptance criteria already written) -> Opus 4.8,
  in Claude Code.

**2.2 The shadow rule:** Fable shadows Opus output on the first two live weekly recap
cycles of the 2026 season only; drop the shadow if clean.

**2.3 Planning-session austerity:** full re-baseline sessions (Fable) are expensive
precisely because they must distrust everything. They are justified only when STATE.md
is suspected stale or a phase boundary is crossed. Keeping STATE.md current (section 4)
is what makes them exceptional. Target: not more than one per month.

**2.4 Never:** Fable for mechanical execution; Opus for constitutional adjudication;
either model re-litigating an adjudicated decision in the Document of Record Part 4A /
Vision Register without founder instruction.

## 3. Session protocol (every session, both tools)

**START - no proposal before verification:**
1. Read this charter (auto-loaded in Claude Code; first read in chat).
2. Read `STATE.md`. Read the session brief.
3. Verify the brief against reality: `git log --oneline -15`; confirm HEAD; spot-check
   every brief claim that lacks a commit hash. Brief claims without hashes are
   UNVERIFIED and must be checked before any work proceeds.
4. If the brief conflicts with git, **git wins**; flag the discrepancy to the founder
   before executing. (Stale-brief hazard: 7+ documented recurrences. The lesson from
   2026-06-09: "data correct on prod is not the same as the code path being guarded in
   the repo" - verify at the layer the claim is about.)
5. Confirm repo identity and re-export env (section 1).

**EXECUTE:**
6. One unit of work per session, one topic per commit. Numbered decisions (D-x) get an
   explicit founder pick before execution - never assumed.
7. Diagnostics before proposals: read actual code and data before suggesting fixes.
8. Gates run before every commit; prove_ci on clean tree before every push.

**END - definition of done (work is NOT complete until all four):**
9. Tests/ruff/mypy green; prove_ci clean (or doc-only path).
10. Observation memo filed in `_observations/` (dated, ASCII-safe filename).
11. **`STATE.md` updated in the same commit series as the work** - discharged items
    marked with commit hashes, new open items registered.
12. Close-out summary to founder: what shipped (hashes), what was discharged, what
    opened, what the next session should be.

## 4. The anti-redo law (single state ledger)

- Each repo carries `STATE.md` at `docs/STATE.md` (registered in the docs Map; root
  allowlist stays at its enforced count). It contains exactly: current HEAD + meaning,
  open units (from the Document of Record), discharged items with hashes, and known
  hazards. It is a READ-MODEL summary, not a narrative - keep it under ~80 lines.
  - **Per-repo realization (amendment v1.1, 2026-06-10).** The ENGINE repo carries
    `docs/STATE.md` as above. The FRONTEND repo discharges the state-ledger role with
    `ROADMAP.md` at repo root (the ordered milestone read-model per
    `_observations/README.md`); it has no `docs/STATE.md`, no docs Map, and no root
    allowlist - that gate apparatus is engine-repo law. Every charter reference to
    "STATE.md" therefore means `docs/STATE.md` engine-side and `ROADMAP.md` frontend-side.
    A brief that says "update STATE.md" against the frontend is satisfied by `ROADMAP.md`;
    do not stand up a frontend `docs/STATE.md` without a further amendment.
- STATE.md is updated as part of every session's commit series (section 3.11). A
  session that completes work without updating STATE.md has not completed the work.
- Git is the read-model; chat artifacts are write-only. No session treats a prior chat
  message, memory summary, or brief as authoritative over `git log` + STATE.md.
- The chat project prompt and project-knowledge corpus point AT STATE.md and the
  Document of Record; they do not duplicate their content (duplication is how staleness
  breeds). Project knowledge retains only the binding set per Document of Record D-D.

## 5. Briefs - the Fable-to-Opus interface

Every execution brief (authored in chat, consumed in Claude Code) contains, mandatorily:
verified HEAD hash at authoring; exact file paths; binary acceptance criteria; gates to
run; an explicit OUT OF SCOPE list; and hashes for every "already done" claim. A brief
missing any of these is returned for completion, not guessed at. Briefs live in
`_observations/` as `session_brief_*.md` per existing convention.

## 6. Documentation hygiene cadence

- `ROADMAP.md` (frontend) and STATE.md (both): updated per-session per section 3.
- Chat project prompt: re-checked at each phase boundary and after any planning session.
- Observation memos: never edited after commit - corrections are new dated memos
  (supersession-then-fold-in pattern, precedent `c4b4436`).
- This charter: reviewed by the founder at phase boundaries; amended per section 9 only.

## 7. Escalation rules (when a session must stop and ask)

Stop and ask the founder before proceeding when: a brief claim fails verification; a
gate fails twice on the same cause; work would touch frozen architecture, a Tier 0-2
document, or an adjudicated Part 4A framing; a D-x decision is unmade; consent-touching
work precedes W.6; or any framing drifts toward engagement/optimization language
(name it, per the cert-5 discipline - catching drift is a success, not an embarrassment).

## 8. Token economy (standing)

- Opus by default; Fable only per section 2. Tight briefs (section 5) are the primary
  token control - exploration is the expensive failure mode, and verification-first
  prevents the costliest one (redoing finished work).
- Engine API: model stays pinned; reverify stays local-only; fresh-generation
  experiments are pre-registered with explicit n. No token telemetry in the creative
  layer (Document of Record, Part 8).

## 9. Amendment log

- v1.0 - 2026-06-09 - Initial charter. Ratified by founder: ____ (date) ____.
- v1.0.1 - 2026-06-09 - Product-plan-of-record pointer updated to the in-repo path
  `docs/SquadVault_Product_Document_of_Record_v2_1.md` (filed and Map-registered in E1.3).
  Founder-approved.
- v1.1 - 2026-06-10 - Section 4 STATE.md note: record the per-repo realization of the
  state ledger (engine `docs/STATE.md`; frontend `ROADMAP.md` at root, no `docs/STATE.md`).
  Founder-instructed. Surfaced by the W.1 Increment 1 ledger session (frontend `ee22e56`).
