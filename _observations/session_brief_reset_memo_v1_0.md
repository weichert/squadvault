# Session Brief — Reset Memo v1.0 (project reset arc)

**Drafted:** 2026-05-07 (Thursday evening, post-`2dda2c2`).

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`

**Phase:** 10 — Operational Observation; project reset arc.

**Shape:** Doc-only session, single artifact, single wave. **No production-path code changes; no diagnostic-script changes; no doctrine outside the reset memo itself.** The session writes one substantive memo that resolves the meta-questions M1–M5 inherited from the gap-audit closure (`2dda2c2`) and formalizes the recalibration arc that ran during the 2026-05-07 session.

**Expected session length:** 90–150 minutes. One commit (the reset memo). M4–M5 may defer to a successor session if the session runs long; M1–M3 are the substantive work and should not be deferred.

**Starting commit:** `2dda2c2`. Verify HEAD before any other action; record at session start.

---

## Why this session, and what it determines

The closure memo at `2dda2c2` halted the project-reset gap audit on its first audit turn. The audit's intended first step was reading the Documentation Map v1.5 to confirm the binding-document list. That read surfaced four findings substantial enough to make per-document audit premature: silent deletion of binding documents from the Map (Finding 0), unresolved Business Plan authority (Finding 1), unexamined deletion of the Compression Rule (Finding 2), and recently-authored documents bypassing the Map entirely (Finding 3).

The closure memo's §6 names five meta-questions the reset memo must resolve before per-document audit can resume:

- **M1.** Is the Compression Rule (or some equivalent priority distinction) still in effect?
- **M2.** What is the Business Plan's authority status?
- **M3.** Which recently-authored documents are binding?
- **M4.** What is the registration mechanism going forward?
- **M5.** Does the Documentation Map need a v1.6?

These are sequenced: M1 is the gating question (how do we know what's binding), M2 builds on M1, M3 builds on M1–M2, M4 follows M3, M5 follows M1–M4. M1–M3 are substantive; M4–M5 are procedural and conditional.

Beyond M1–M5, the reset memo carries a second substantive load: the recalibration arc that ran during the 2026-05-07 session is currently held in conversation context and memory but not formalized in any binding artifact. Today's framings — integrity principles binding, scope restrictions retired, Business Plan as binding-vision-source pending M2, Phase 11 (Product Surface) active, niche-agnosticism architecturally backed via clean import graph and platform-agnostic `canonical_events` schema — must move from conversational memory into a doctrine document. The reset memo is the natural vehicle: M2 already deliberates the Business Plan, and M1–M3 already deliberate scope; the recalibration framings sit alongside them and get formalized in the same artifact.

Without this session, future contributors (the next Claude-session, Steve in three weeks, an engineer onboarding from outside) would read the Constitution, the Compact, the Operational Plan, and the existing addenda and reach a strict-construction conclusion that the recalibration arc explicitly retired this evening. The reset memo's existence prevents that drift.

---

## Predecessor work the reset memo builds on

- **`2dda2c2`** — the closure memo. Inheritance source for M1–M5. **Read end-to-end at session start before authoring.**
- **`9a4fa89`** — gap audit session brief. Documents the project-reset arc's first session attempt and the audit's intent. The reset memo's framing of "what the gap audit was for" derives from this brief.
- **`1cf4142`** — Tier 5 doctrine v1.0. Two roles: (a) shape precedent — provisional doctrine in `_observations/` with promotion gated on empirical validation; (b) instance evidence for Finding 3 — a recently-authored binding document that bypassed the Map entirely.
- **`14c6003`** — Weekly Recap Context Temporal Scoping Addendum promotion from `_observations/` to `docs/addenda/`. Cited in Finding 3 as the only recent precedent for `_observations/`-to-`docs/` promotion. Sets the pattern Tier 5 v1.0 follows.
- **The recalibration arc conversation (2026-05-07).** Captured in the prior-session summary attached to this brief; not committed as a formal artifact (intentionally — the reset memo is the formalization). Establishes integrity-vs-scope distinction, multi-modal multi-tenant vision affirmation, niche-agnosticism architectural backing.
- **The Business Plan upload event.** Steve uploaded the Business Plan during the session; its §3 (Vision & Why Now), §6 (Core Features & Functionality), and Founder's Letter articulate the multi-modal multi-tenant social-surface vision Phase 11 honors. M2 deliberates the plan's authority status using the plan itself as evidence.
- **Documentation Map v1.4** (`SquadVault_Documentation_Map_and_Canonical_References_v1_4_1.pdf` in project knowledge) and **v1.5** (`SquadVault_Documentation_Map_v1_5__1_.docx`). The two Map versions are the evidentiary base for M1 (Compression Rule comparison), M3 (registered-document set comparison), and M5 (what v1.6 would correct).
- **Working-process commitments accumulated 2026-05-07 evening:** multi-frame deliberation when frames disagree, confidence labeling on substantive claims, domain-limitation flagging when advising outside high-confidence areas, one-major-artifact-per-session default. Not codified in any memo. The reset memo may codify them or leave them in conversation context — see Q3 below.

---

## Scope

### In scope

The reset memo deliberates and resolves the following surface:

#### M1 — Compression Rule status

The reset memo picks Reading A (the Compression Rule still applies, just unstated), Reading B (the Compression Rule was retired without replacement), or articulates a third option (e.g., reinstate v1.4 conventions explicitly with v1.5's structural improvements layered on top). It then writes the doctrine explicitly: which tiers are binding, which are reference-only, how the project-day-to-day decides what to load as authority. Resolution shape from closure memo §6: *"Tier 0 through Tier X are binding; Tier X+1 through Tier 5 are reference-only, invoked explicitly,"* or *"All documents in all tiers are binding, with conflict resolution by [explicit ordering]."* Either is acceptable; ambiguity is not.

#### M2 — Business Plan authority

The reset memo picks: binding-vision-source / reference-only / retired / fourth option. If binding-vision-source, carve out which sections bind (vision, founding intent, multi-modal multi-tenant scope) and which do not (growth projections, ARPU/CAC framework, Year-3 revenue mechanics). If retired, explain why the recalibration arc's treatment of it as binding-vision-source was an error and what the actual binding-vision-source is instead. The frames named in closure memo §3 — venture-pitch artifact / vision-source / superseded — are the deliberation surface.

#### M3 — Recently-authored binding documents

For each of the 8–10 unregistered documents enumerated in closure memo §5: doctrine answer of binding / reference-only / operational-scaffolding-not-binding. The set as captured at brief authoring time: Platform & Writer's Room Compact v1.0; Operational Plan v1.1; Platform Adapter Contract Card v1.0; Canonicalization Policy Addendum v1.0 and Canonicalization Semantics Addendum v1.0; EAL Persistence Clarification Addendum v1.0 and Editorial Attunement Layer — Core Engine Addendum v1; Weekly Recap Context Temporal Scoping Addendum v1.0; Internal Note — Why The Editorial Attunement Layer Exists; Tier 5 Live Observation Cadence Doctrine v1.0. This list is provisional; session-start verification may surface additional documents (or remove ones the audit's wider sweep determines are reference-only).

#### M4 — Registration mechanism going forward (procedural; may defer)

The reset memo names a session-discipline that ensures the Map is updated when new binding documents ship. Possible mechanisms: a Map-update step in the session-completion checklist; a pre-commit gate that fails if `docs/` gets a new top-level document without the Map being touched in the same commit; a quarterly Map-review cadence. The choice is procedural; the rationale matters more than the specific mechanism. M4 may defer to a successor session if M1–M3 deliberation runs long.

#### M5 — Documentation Map v1.6 commissioning (conditional; may defer)

The reset memo commissions the Map v1.6 as a follow-on artifact (does not author it inline). M5's resolution is one paragraph at most in the reset memo: *the Map needs a v1.6 that does X, Y, Z; commissioned as standing-backlog item N; predecessor: this memo.* M5 may defer if M4 defers.

#### Recalibration arc formalization

Distinct from M1–M5 but inseparable from them. The reset memo states explicitly:

- The Constitution's **integrity principles** are binding and load-bearing: facts immutable and append-only, narratives derived never fact-creating, AI assists humans approve publication, silence over speculation. The substrate's **no-analytics / no-optimization / no-engagement-loops / no-prediction** rule sits in this same integrity tier and is not retired by the recalibration arc.
- The Constitution's **scope restrictions** were build-phase scaffolding that has been **retired**: single-league, single-tone, text-only, no frontend, no multi-modal, no discussion surface. These were boundaries on the substrate work that is now complete; they are not constraints on what SquadVault is.
- The Business Plan's **multi-modal multi-tenant social-surface vision** is **affirmed, not deferred**, subject to M2's specific carve-outs.
- **Niche-agnosticism** is architecturally backed: `core/` import-graph is clean of `mfl/` and `recaps/writing_room/`; `canonical_events` schema is platform-agnostic; fantasy-football-specific surface inside `core/` is bounded (~10–15%) and relocatable. The Compact's niche-agnosticism claim is empirically supported.
- **Phase 11 (Product Surface)** is the active phase. Phases 12+ contemplate the larger Business Plan vision (multi-modal, multi-tenant, social-surface, multi-tone Tone Engine, Hall of Fame & Shame, league chat replays).

This formalization is not deliberation; the recalibration arc has already settled it. The reset memo records it.

#### Phase 11 framing (lighter touch than M1–M5)

The reset memo names Phase 11 as the active phase, what its substantive surface is in v1.0 terms, what it forbids itself from adding, and how it relates to Phases 12+. The Apple-discipline framing proposed during the recalibration arc — *constraint over breadth; ship one or two surfaces exquisitely, not five at minimum-viable; every Phase 11 surface gets its own constitutional memo* — is the candidate doctrine. The reset memo either adopts it or names a different framing. Phase 11 surface specification (recap-reading session, etc.) is **out of scope**; the reset memo names that Phase 11 exists, not what its surfaces are.

#### The disruption-vs-artisan question (engaged or explicitly deferred)

Noted during the recalibration arc as a real question that Phase 11 work will start to answer empirically. The reset memo either deliberates it inline or queues it for a successor session. **Default: defer**, with a one-paragraph naming so the question is in the binding artifact rather than only in conversation context.

### Out of scope

- **The per-document gap audit.** Blocked pending M1; resumes only after the reset memo ships.
- **Documentation Map v1.6 itself.** Conditional follow-on; separate session. M5 commissions it but does not author it.
- **Phase 11 surface specification.** The reset memo names that Phase 11 exists; surface specification (the recap-reading session, the first product-surface artifact) happens in successor sessions, each with its own constitutional memo per the Apple-discipline framing.
- **New process infrastructure.** Working-process commitments accumulated tonight (multi-frame deliberation, confidence labeling, domain-flagging) may be referenced; codification into a separate process-doctrine document is not the reset memo's job. Q3 below resolves whether they appear inline in the reset memo or remain in conversation context until empirically demanded.
- **Codebase-vs-doctrine reconciliation.** Separate concern, downstream of Map v1.6.
- **Re-litigation of the recalibration arc.** The integrity-vs-scope distinction, the Business Plan as binding-vision-source, the niche-agnosticism architectural backing — these are inputs to the reset memo, not outputs. The reset memo records them; it does not reopen them.

---

## Sections the reset memo will likely cover (foreshadow only)

The reset memo follows the doctrine-memo shape established by `1cf4142`. Likely structure:

- **§1 — TL;DR.** The recalibration arc in two paragraphs; the M1–M5 resolutions in one paragraph each.
- **§2 — The recalibration arc.** What was held implicitly through 2026-05-06; what shifted on 2026-05-07; what's now binding. Integrity-vs-scope distinction, niche-agnosticism architectural backing.
- **§3 — M1: Compression Rule status.** Reading selected; rationale; explicit doctrine for how new binding documents register and how the project decides what to load.
- **§4 — M2: Business Plan authority.** Status decision; per-§ carve-outs; rationale.
- **§5 — M3: Recently-authored binding documents.** Per-document classification.
- **§6 — M4: Registration mechanism.** Procedural doctrine. (May defer.)
- **§7 — M5: Map v1.6 commissioning.** (May defer.)
- **§8 — Phase 11 framing.** Active-phase status; Apple-discipline candidate; Phases 12+ relationship; surface-specification deferral to successor sessions.
- **§9 — The disruption-vs-artisan question.** Engaged or named-and-deferred.
- **§10 — Standing-backlog updates and authority position.** What the reset memo's existence changes about the standing backlog; where the reset memo sits relative to Constitution / Compact / Operational Plan.
- **§11 — Methodology notes.** Reset-memo-as-formalization-of-arc precedent; M1–M5 sequencing observation; multi-frame deliberation as a working-process discipline.
- **§12 — Files and commits referenced.**

The brief does not prescribe section ordering or content beyond this outline. The reset memo's authoring session decides the order, lengths, and which sub-sections each section needs.

---

## Filing decision

**Default:** `_observations/OBSERVATIONS_2026_05_<DD>_RESET_MEMO_V1_0.md`. Matches Tier 5 doctrine's filing precedent (`1cf4142`) — provisional doctrine in `_observations/` with promotion gated on either (a) a successor session validating the framings empirically, or (b) a successor reset memo refining the v1.0. The act of committing it is not the act of promoting it to canon.

**Alternative:** `docs/00_governance/SquadVault_Reset_Memo_v1_0.md`. The reset memo could be argued as governance-level doctrine that should sit at the highest tier from day one — actual canon, not observation. The argument for this filing is that M1's resolution is a governance doctrine (which tiers bind) and should not sit in `_observations/` once the reset memo lands.

**Argument for the default:** the reset memo is v1.0 of an iterating doctrine surface. Phase 11's first surfaces will surface empirical pressure on M1–M3 resolutions. A v1.1 / v1.2 cycle in `_observations/` lets the doctrine refine without canon-promotion friction. Promotion to `docs/00_governance/` happens after one or two real Phase 11 surface sessions validate the framings.

Q1 below resolves which filing is correct. The brief defaults to `_observations/`.

---

## Open questions for session start

### Q1 — File location: `_observations/` or `docs/00_governance/`?

Default: `_observations/`. Alternative: `docs/00_governance/`. See Filing Decision above. Resolve at session start before authoring.

### Q2 — M4–M5 deferral threshold

If M1–M3 deliberation has consumed ~90 minutes by the time the session reaches M4, defer M4–M5 to a successor session. If M1–M3 was tight (~60 minutes), pursue all five. Decision rule: at the M4 entry point, look at total session time and remaining cognitive budget; defer if either is constrained.

### Q3 — Working-process commitments codification

The multi-frame deliberation, confidence labeling, and domain-limitation flagging accumulated 2026-05-07 evening have not been codified anywhere. Three options: (a) codify in the reset memo's §11 Methodology Notes; (b) commission a separate process-doctrine memo as a follow-on; (c) leave as conversation-context-only until empirically demanded. **Default: (c)** — per the over-institutionalization-reflex anti-drift, *"thorough summary is sufficient."* Codify only when something has demonstrably failed without codification.

### Q4 — Disruption-vs-artisan question: deliberate inline or defer?

Default: defer with one-paragraph naming. The question is real but Phase 11 work will produce the empirical evidence that makes it tractable. Named-and-queued is sufficient for v1.0.

### Q5 — Authority hierarchy

Where does the reset memo sit relative to the Constitution, the Compact, the Operational Plan v1.1? Subordinate (the Constitution still tops authority, the reset memo is one document among many)? Successor (the reset memo synthesizes and supersedes prior governance doctrine)? Synthesis-document (the reset memo names the relationships among prior documents without superseding any)? **Default: synthesis-document.** The Constitution remains the integrity-principles source; the Compact remains the niche-agnosticism + Writer's Room boundary source; the Operational Plan v1.1 remains the operational-track source; the reset memo names how they relate post-recalibration.

### Q6 — Memo length budget

Tier 5 doctrine v1.0 is 246 lines. The reset memo's surface is broader (M1–M5 plus recalibration formalization plus Phase 11 framing). Suggested target: **350–500 lines.** If the draft exceeds 600 lines, look for sections to defer (M4–M5 are the natural deferral candidates). If the draft comes in under 250 lines, reconsider whether all five M-questions actually got substantive treatment.

---

## Anti-drift discipline

1. **Re-grounding is session step 0.** Verify HEAD, baseline tests (1958 / 2 expected), ruff clean, mypy clean (60 files expected). Read `2dda2c2` end-to-end before authoring. The brief is dated 2026-05-07; if the reset-memo session happens days or weeks later, predecessor work may have shifted.

2. **The reset memo is doc-only.** Zero production-path changes. Zero diagnostic-script changes. Zero test changes. The memo references file paths and commit hashes; it does not modify them.

3. **Strict-construction reflex.** If during authoring Claude shows up treating "no frontend, no multi-modal, no discussion surface" as binding rather than retired, push back. These were build-phase scaffolding that the recalibration arc explicitly retired. The integrity principles are binding; those scope restrictions are not.

4. **Search-result framing bias.** Retrieval surfaces snippets; snippets over-represent whichever framings match query terms. If the reset memo's M1–M3 deliberations appear to be reasoning from snippets rather than full documents, name it and load the full document. Specifically: M2 (Business Plan) and M3 (per-document binding status) both require full-document reads, not snippet-driven inferences.

5. **Over-institutionalization reflex.** If during authoring Claude proposes elaborate process infrastructure (CURRENT_STATE.md, opener templates, rituals codified in writing) for problems a thorough summary would solve, push back. Tonight's correction was *"thorough summary is sufficient."* Hold that line. The reset memo formalizes what's binding; it does not invent new procedural rituals.

6. **Momentum past gates.** If the session runs long and Claude wants to ship M4–M5 under fatigue, defer them. The "ship 60% cleanly than 100% under fatigue" discipline that governed the gap audit applies here. M1–M3 are the substantive work.

7. **Disruption-shaped framings.** If Phase 11 framing (§8) starts pulling toward growth-metrics, engagement-loops, or scale-mechanics without explicit constitutional accounting, name it. The integrity principles are binding; the substrate's "no analytics, no optimization, no engagement loops, no prediction" rule remains in force regardless of recalibration. Phase 11 honors the Business Plan's vision through the Constitution's discipline, not by relaxing the discipline.

8. **Multi-frame deliberation discipline.** When M1–M3 deliberations surface disagreement among engineering / product / editorial / process frames, surface the disagreements explicitly. Let the synthesis be visible. Do not collapse to a single frame's preferred answer.

9. **Confidence labeling on substantive claims.** *High confidence* with grep-evidence or direct read; *medium* with reconstruction or inference; *low* without strong evidence. The reset memo's resolutions should themselves be confidence-labeled where appropriate (e.g., M1 may be high-confidence if the rationale is grounded in the v1.4 Map's explicit text; M2's per-§ carve-outs may be medium; the disruption-vs-artisan stance is low).

10. **Domain-limitation flagging.** When M2 (Business Plan authority) or §8 (Phase 11 framing) requires reasoning about product-strategy or marketing claims, name the domain limitation rather than performing expertise. Steve holds product judgment; Claude scaffolds.

11. **Bulletproof memo-write form** per memory edit #21. `python3 <<'PYEOF'` with `pathlib.Path('...').write_text(MEMO, encoding='utf-8')` and MEMO as a triple-quoted raw string. No triple-backticks at column 0, no delimiter literals at column 0 in body.

12. **Apply-then-verify** per memory edit #22. After the heredoc-write step, an explicit verify step (`wc -l`, `head`, `tail`) runs before the staging gate. Lint+test gates and `git commit` / `git push` MUST be in separate paste turns; never chained with `&&`.

13. **One major artifact per session default.** The reset memo is the artifact. No second commit unless empirically demanded by the session's work itself (e.g., a typo fix in `2dda2c2` discovered during the M1 read).

---

## Standing backlog (carries forward post-this-session)

If the reset memo ships v1.0 with M1–M5 all resolved:

1. **(THIS SESSION when run)** Reset Memo v1.0 — RETIRED at this session's commit hash.
2. **(UNBLOCKED → ACTIVE)** Gap Audit Document Reconciliation v1.0 — predecessor: this session. Per-document audit can now proceed against the M1-resolved binding-document scope.
3. **(NEW)** Documentation Map v1.6 — commissioned by reset memo §7 (M5). Predecessor: this session. Authoring session is separate.
4. **(NEW)** Phase 11 surface specification (recap-reading session as candidate first surface) — predecessor: reset memo §8 (Phase 11 framing).
5. (Carry-forward, Tier-5-monitored) Section 10 Q1 Bug 1, SCORE_VERBATIM legacy-drift, player-streak verb inversion, Cat 3c row-76, snap-outcome detection, NOTABLE-pass alphabetical lockout, Bug 1 classifier current-week scope, Tier 5 doctrine v1.1 trigger, Framing B wrapper, priority-list mechanism redesign.

If the reset memo ships v1.0 with M1–M3 resolved and M4–M5 deferred:

1. **(THIS SESSION when run)** Reset Memo v1.0 (M1–M3 only) — RETIRED at this session's commit hash.
2. **(UNBLOCKED → ACTIVE)** Gap Audit Document Reconciliation v1.0 (per #1 in the all-resolved case).
3. **(NEW, ACTIVE)** Reset Memo v1.0 successor (M4 + M5) — predecessor: this session. Successor session resolves the deferred procedural questions.
4. (Documentation Map v1.6 commissioning blocked pending M4 + M5.)
5. Remaining items per the all-resolved case.

---

## Opening move (paste into terminal at session start)

    cd ~/projects/squadvault-ingest-fresh
    git fetch origin
    git rev-parse HEAD
    git log --oneline -8
    git status
    PYTHONPATH=src python -m pytest Tests/ -q 2>&1 | tail -3
    ruff check src/ Tests/
    mypy src/squadvault/core/ 2>&1 | tail -3

    ls _observations/ | grep -iE "reset|recalibration|governance" | head
    grep -rn "Reset Memo\|recalibration arc" _observations/ docs/ 2>/dev/null | head

Then read `2dda2c2` end-to-end. Then resolve Q1 (file location), Q2 (M4–M5 deferral threshold), Q3 (working-process codification), Q4 (disruption-vs-artisan engagement), Q5 (authority hierarchy), Q6 (length budget). Then author per the M1–M5 surface plus recalibration formalization plus Phase 11 framing.

---

## The point

The Documentation Map drift surfaced four findings on a doc-only audit's first turn. The audit halted. The closure memo at `2dda2c2` articulated five meta-questions. The reset memo resolves them — three substantively (M1–M3), two procedurally (M4–M5).

Beyond unblocking the audit, the reset memo formalizes the recalibration arc that ran 2026-05-07: integrity principles binding, scope restrictions retired, Business Plan as binding-vision-source pending M2, Phase 11 active, niche-agnosticism architecturally backed. Without the reset memo, future sessions would operate from conversational memory of shifts that never made it into a binding artifact — and a strict-construction reading of the existing canon would reach conclusions the recalibration arc explicitly retired.

The reset memo is v1.0. It will refine. The act of writing it is the closure of a doctrine-shape gap that's been carried as conversational-only since Thursday evening.

Doctrine first. Phase 11 second. Map v1.6 third.
