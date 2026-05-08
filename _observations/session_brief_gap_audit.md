# Session Brief — Gap Audit (Document Reconciliation Audit v1.0)

**Predecessor context:**

- Tier 5 doctrine v1.0 shipped at `1cf4142` (2026-05-07) — `_observations/OBSERVATIONS_2026_05_07_TIER_5_LIVE_OBSERVATION_DOCTRINE.md`.
- Project recalibration arc (Thursday evening 2026-05-07) established: integrity principles binding, scope restrictions retired, Phase 11 (Product Surface) is the new active phase, niche-agnosticism architecturally backed, Phases 12+ contemplate the multi-modal multi-tenant vision the Business Plan describes.
- Architectural finding from the recalibration arc: `core/` import-graph is clean of `mfl/` and `recaps/writing_room/`; `canonical_events` schema is platform-agnostic; fantasy-football-specific surface inside `core/` is bounded and relocatable. Documented evidence supports the Compact's niche-agnosticism claim.

**Shape:** Doc-only session, single wave. **No production-path code changes; no new doctrine.** The session produces one artifact: a structured gap audit memo that walks every binding canonical document, summarizes what each one actually says (re-read, not remembered), identifies conflicts and silences, and produces an evidentiary substrate the reset memo will cite. The audit does not render reconciliation verdicts — that is the reset memo's job, downstream. The audit's discipline is description, not synthesis.

## Why now

The recalibration arc surfaced that two binding documents — the Business Plan (2024) and the Constitution (evolved through 2025-2026) — have been operating in tension for months. The "What We Are Not" memo and the Operational Plan v1.1 sit between them, occasionally reading as Constitution-aligned and occasionally as Business-Plan-aligned. The Operational Plan §10 was cited in a recent session as forbidding multi-modal expansion as Phase F+; the Business Plan §6 lists multi-modal as core feature set. Both documents are signed off in the project. Neither has formally retired the other.

The reset memo will need to resolve this, but it cannot resolve it without an evidentiary base that names the conflicts concretely. A reset memo that cites "the Constitution says X but the Business Plan says Y" needs the exact §s and quotes to be auditable. The gap audit produces that evidentiary base.

The audit also catches a class of error worth surfacing: prior advisory work has been operating with implicit framings that turned out to be wrong, sourced partly from search results that surfaced certain document sections preferentially. A disciplined re-read of every binding document in sequence, in one session, breaks that pattern. The audit serves both the reset memo's evidentiary needs and the re-grounding of project-wide understanding.

## What the audit covers (in scope)

Every binding canonical document in the project. Not every document — binding documents only. The distinction matters because some documents are reference material (Voice Profile, Recap Review Heuristic, individual contract cards) and bind specific surfaces rather than project direction; they do not need reconciliation against each other. Binding documents do.

The binding-document list as provisionally identified at brief authoring time (to be confirmed at session start by reading the Documentation Map v1.5 and any successor; the Map is the source of truth for what counts as binding):

1. **SquadVault Business Plan** (2024 founding document)
2. **SquadVault Canonical Operating Constitution v1.0**
3. **Platform & Writer's Room Compact v1.0**
4. **SquadVault Operational Plan v1.1**
5. **SquadVault — What We Are Not — Platform Guardrails v1.0**
6. **SquadVault Stop Before Suggesting X Guardrails v1.0**
7. **SquadVault Data Ethics and Trust Positioning Memo v1.0**
8. **SquadVault Implementation Readiness Package (IRP) v1.0**
9. **SquadVault Development Playbook MVP v1.1**
10. **SquadVault Second Module Qualification Checklist v1.0**
11. **SquadVault AI Development Rules of Engagement v1.0**
12. **Platform Adapter Contract Card v1.0**
13. **Canonicalization Policy Addendum v1.0** and **Canonicalization Semantics Addendum v1.0**
14. **EAL Persistence Clarification Addendum v1.0** and the **Editorial Attunement Layer — Core Engine Addendum v1**
15. **Weekly Recap Context Temporal Scoping Addendum v1.0**
16. **Internal Note — Why The Editorial Attunement Layer Exists**
17. **Tier 5 Live Observation Cadence Doctrine v1.0** (shipped 2026-05-07; included for completeness, expected to be CONSISTENT with itself but should be checked)

This list is provisional. The Documentation Map v1.5 may surface additional binding documents not enumerated here, or identify items above as non-binding. Session-start verification (Q1) confirms the list before the per-document analysis begins. If the Documentation Map itself has drifted from current reality after several months of new documents shipping, the audit's binding-doc list may need to be derived from a wider sweep — that is itself a finding worth recording.

## What the audit covers (out of scope)

- **Reference documents.** Voice Profile, Recap Review Heuristic, contract cards for individual signals (Signal Scout, Tier1 Signal Derivation, etc.), Operational Scenarios docs, Onboarding Brief. These are downstream of binding docs and do not need reconciliation against each other.
- **Implementation memos.** All `OBSERVATIONS_*.md` files in `_observations/`. They document specific findings and closures; they are not binding doctrine.
- **Session briefs.** Including this one. They document scoping decisions for individual sessions, not project-wide direction.
- **The codebase itself.** A separate architectural state document (downstream of the reset memo) handles code-vs-doctrine reconciliation. The audit is doc-vs-doc.
- **Verdict-rendering.** The audit names conflicts; it does not resolve them.

## Audit dimensions

For each binding document, the audit captures:

1. **Date and version.** When was this document authored and most recently revised? Is it the v1.0 or has it iterated?
2. **Stated intent.** What does the document claim as its purpose, in its own words (one paragraph)?
3. **Authority position.** Does the document claim to bind, supersede, or extend other documents? Is it explicit about what it does not govern?
4. **Scope claims.** What surface area does the document address? What does it explicitly include, explicitly exclude, leave silent on?
5. **Conflicts with peers.** Where does this document say something that another binding document says differently? Cite both §s.
6. **Silences.** What questions does this document leave unaddressed that another binding document does address?
7. **Drift indicators.** Where has the codebase or recent project work diverged from what this document claims?

Output format: structured per-document section for items 1-4, followed by a **Conflicts Matrix** that crosses every pair of documents and notes where conflicts exist (items 5-6), followed by a **Drift Inventory** for item 7.

## Output specifications

- **File:** `_observations/OBSERVATIONS_2026_05_<DD>_DOCUMENT_RECONCILIATION_AUDIT.md`
- **Length:** Substantial. Probably 400-600 lines. The Tier 5 doctrine memo at 245 lines is a doctrine-shape document; the audit is an evidentiary-shape document and is naturally longer. If the audit comes in under 300 lines, that is a signal of insufficient thoroughness.
- **Structure:** §1 framing and methodology, §2 binding-document list with rationale, §3 per-document analysis (one subsection per binding doc), §4 conflicts matrix, §5 silences inventory, §6 drift indicators, §7 named follow-ons for the reset memo.
- **Tone:** Descriptive, not prescriptive. The phrase "this conflicts with X" appears; the phrase "this should be resolved by doing Y" does not.

## Methodology constraints

- **Read each binding document end-to-end before writing about it.** No relying on search-result snippets or memory. Quote at the level required to make conflicts visible; conflicts are visible only at the level of specific phrasing.
- **Bulletproof memo-write form** per memory edit #21 for the audit memo itself.
- **Apply-then-verify discipline** per memory edit #22: any heredoc-write step is followed by an explicit verify-step before subsequent gates run.
- **One commit per document section** if the audit becomes long enough that committing per-document makes sense. Otherwise, single commit at session end.
- **Time-box.** This session has a soft cap of 4 hours of work. If the audit is incomplete at the cap, ship what is complete with a "remaining documents to be audited in successor session" §, and queue the rest. Better to ship 60% of an audit cleanly than 100% under fatigue.

## What "session complete" looks like

The audit memo is committed and pushed. It contains:

- Per-document analysis for every binding doc identified at session start.
- A conflicts matrix that names every pairwise conflict, even minor ones (the reset memo decides what is substantive; the audit's job is comprehensive coverage).
- A silences inventory naming questions that no binding doc addresses.
- A drift inventory naming places where the code or recent work has moved past what binding docs say.
- A §7 follow-on list for the reset memo: a numbered list of "the reset memo will need to resolve X" items, derived from the conflicts matrix.

The audit is not committed to `docs/`. It lands in `_observations/` because it is evidentiary, not doctrine. The reset memo (next session) is the doctrine.

## Standing-backlog status

This audit becomes item #1 in the post-Tier-5 standing backlog, displacing the substrate items as the active work surface. The substrate items do not go away — they remain as Tier-5-monitored background work — but they are not foreground priorities until Phase 11 implementation begins.

## Open questions for session start

- **Q1: Documentation Map v1.5 verification.** Read it first; confirm the binding-document list. If documents listed there as binding are not in §"What the audit covers" list, add them. If documents in this brief's list are not in the Map, decide whether they should be (and flag the Map for revision).
- **Q2: Audit memo file naming.** `OBSERVATIONS_2026_05_<DD>_DOCUMENT_RECONCILIATION_AUDIT.md` is the proposed name. If the audit ends up multi-session, the successor sessions get `_PART_2`, `_PART_3` suffixes. Confirm at session start.
- **Q3: Time-box behavior on incomplete audit.** If the 4-hour cap hits with documents still un-audited, do we ship a partial audit and queue the rest, or do we extend the session? Default: ship partial. Confirm at session start.

## Anti-drift discipline

- This is a doc-only session. No production code changes. No new doctrine. No reset-memo writing inside this session.
- The audit describes; it does not synthesize.
- Conflicts are named at the level of citation. "Document A §X says P; Document B §Y says Q; P and Q are in tension because R." Not "I think A is right and B is outdated."
- If a conflict is genuinely ambiguous — readable as both compatible and conflicting depending on charitable interpretation — name it as ambiguous and document both readings. Do not force a verdict.
- **Closure-memo discipline.** If the audit surfaces a finding that a binding doc has been silently superseded by another binding doc (e.g., the Operational Plan v1.1 supersedes parts of the Business Plan implicitly), name that as a finding for the reset memo to formalize, not as a verdict the audit renders.
- **Multi-frame deliberation discipline** (per the working-process refinement at session ratification). When the audit surfaces a conflict that different expert framings (engineering, product, editorial, process) would interpret differently, name the framings explicitly and let the reset memo synthesize. The audit's job is to make the disagreement visible, not to collapse it.

## Session opener

After preamble check (HEAD verification, working tree clean, baseline tests, ruff/mypy clean), read this brief end-to-end. Decide whether anything in it needs revision before proceeding. If revision is needed, revise and commit the revised brief first, then start the audit. If the brief is ratified as-is, commit it as-is, then start.

The first audit step is reading the Documentation Map v1.5 to confirm the binding-document list. From there, work through the binding documents in approximate authority order: Business Plan first (oldest, most ambitious), then Constitution (evolved foundation), then the implementation framework documents (Compact, Operational Plan, IRP, Development Playbook), then the guardrail documents (What We Are Not, Stop Before Suggesting X, Data Ethics), then the addenda. Tier 5 doctrine last, as a self-consistency check.

## Predecessor commit

This brief is committed as the predecessor artifact for the gap audit session. The audit memo cites this brief as `_observations/session_brief_gap_audit.md` at the audit's commit hash.
