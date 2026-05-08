# OBSERVATIONS — Gap Audit halted at Finding 0

**Drafted:** 2026-05-07.
**HEAD at draft:** `9a4fa89` (gap audit session brief commit).
**Phase:** 10 — Operational Observation; project reset arc.
**Position in plan:** First substantive artifact of the project reset arc beyond the gap audit's session brief itself. Documents why the gap audit halted on its first audit turn and what the reset memo must resolve before per-document audit can resume.

---

## 1. TL;DR

The gap audit, scoped at `_observations/session_brief_gap_audit.md` (`9a4fa89`), began its first audit step by reading the Documentation Map v1.5 to confirm the binding-document list. The Map read surfaced four findings substantial enough that per-document audit became premature. The audit halted at Finding 0; this closure memo captures the findings and the meta-questions they raise for the reset memo to deliberate. Per-document audit resumes only after the reset memo resolves the binding-document scope question.

The discipline this memo follows: *closure-memo-for-halted-audit is a legitimate session artifact*, parallel to closure-memos-for-non-findings introduced as Norm 3 at `6740014`. Stopping the audit because the meta-question outranks the audit's discipline is itself a finding, and the finding deserves an artifact.

---

## 2. Finding 0 — The Documentation Map v1.5 has drift, including the silent deletion of binding documents

Two versions of the Documentation Map were located in project knowledge:

- `SquadVault_Documentation_Map_and_Canonical_References_v1_4_1.pdf` — predecessor, included a "Compression Rule" and a richer Tier-5 entry list.
- `SquadVault_Documentation_Map_v1_5__1_.docx` — current authoritative version, dated implicitly post-2026-04-27 since Rivalry Chronicle Contract Card v1.0 is annotated "← NEW".

Comparison of the two Maps:

**v1.5 vs v1.4 — what was removed:**

- Tier 5 entry **"Business Plan & Appendices"** — present in v1.4, removed in v1.5.
- Tier 5 entry **"First 90 Days Post-MVP Playbook"** — present in v1.4, removed in v1.5.
- Tier 5 entry **"Sprint Plans & Build Phase Artifacts"** — present in v1.4, removed in v1.5.
- Tier 5 entry **"Vision & Architecture Drafts (Non-Binding)"** — present in v1.4, removed in v1.5.
- Tier 4 entry **"First 90 Days Post-MVP Playbook"** — present in v1.4, removed in v1.5.
- The **Compression Rule** — explicit in v1.4, deleted in v1.5 without replacement.
- The **Canonical Declaration** — explicit in v1.4 ("In the event of conflict, the Canonical Operating Constitution and subordinate Contract Cards take precedence"), deleted in v1.5 without replacement.

**v1.5 vs v1.4 — what was added:**

- Tier 2 entry **"Writing Room — Selection Set Schema (v1.0)"** — present in v1.5, not in v1.4.
- Tier 2 entry **"Rivalry Chronicle — Contract Card (v1.0) ← NEW"** — present in v1.5, not in v1.4.
- **"Conceptual Components (Non-Contract)"** §, listing Social Layer as deferred — present in v1.5, not in v1.4.

The deletions in v1.5 are not minor housekeeping. The Business Plan's removal from the Map is a governance-level decision that has not been documented in any commit memo I can locate. The Compression Rule's deletion changes the meaning of what is binding for every document in Tier 3-5 — a far-reaching implicit change. No accompanying memo explains the rationale for either change.

This is the pattern the placeholder doctrine surfaced earlier today (`1cf4142` §1 TL;DR): "named concepts that are not verified at every reference drift the same way that quantitative figures drift." The Documentation Map is itself subject to this drift, and the Map was authored as the corrective for documentation-state drift. The corrective drifted. This is not pejorative; it is the same shape of pattern that produces useful audits.

---

## 3. Finding 1 — The Business Plan's authority status is unresolved

The Business Plan was the founding document for SquadVault, dated 2024 per its own framing. It articulates the multi-modal, multi-tenant, social-surface, multi-tone product vision that today's recalibration arc identified as the *destination* the substrate work was building toward.

The Documentation Map's treatment:

- v1.4: listed as Tier 5 ("Archival & Reference Documents"), with the Compression Rule applying ("Tier 3-5 documents are reference-only and must not be treated as authority unless explicitly invoked").
- v1.5: removed entirely. Not in any tier.

Today's recalibration arc treated the Business Plan as binding-vision-source — the document whose original ambition is being honored by Phase 11. That treatment reads against the Documentation Map's classification, in both v1.4 and v1.5 forms.

The reset memo must resolve, with explicit doctrine: is the Business Plan binding (today's recalibration framing), reference-only (v1.4 framing), retired (v1.5 framing by omission), or some fourth status the project has not yet articulated?

This is the most important meta-question the audit surfaced. Several frames sharpen the question:

- **The Business Plan as venture-pitch artifact.** The plan was authored for prospective investors and strategic partners. Its growth language (ARPU, CAC, churn, Year-3 revenue projections) reads as venture-pitch rather than as binding doctrine. Under this frame, the Business Plan was never binding; it was an aspirational external-facing artifact.
- **The Business Plan as vision-source.** The Founder's Letter and §3 (Vision & Why Now) and §6 (Core Features & Functionality) describe the product the substrate has been built to serve. Under this frame, the Business Plan binds the *product direction* even if its growth-mechanics sections do not.
- **The Business Plan as superseded.** The Constitution and Compact were authored later and may, by their substance, have superseded the Business Plan's binding portions. Under this frame, the Business Plan is properly retired and the Map's v1.5 omission is correct.

The reset memo deliberates among these readings. The audit does not.

---

## 4. Finding 2 — The Compression Rule's deletion is unexamined and has enormous implications

The v1.4 Documentation Map contained this rule:

> Compression Rule:
> Only Tier 0–2 documents should be loaded by default during design, development, or AI-assisted reasoning.
> Tier 3–5 documents are reference-only and must not be treated as authority unless explicitly invoked.

Under this rule, the binding document set was approximately 10 documents (Tier 0 + Tier 1 + Tier 2). The remaining 14-plus documents in Tier 3-5 were *reference-only* — to be consulted when explicitly invoked, not loaded as authority during normal work.

The v1.5 Map removed this rule entirely. The v1.5 tier structure preserves the labels Tier 0 through Tier 5 (with Tier 5 still labeled "Archival & Reference"), but the explicit rule about how to *use* the tiers is absent.

Two readings of the deletion are possible:

- **Reading A: The Compression Rule still applies, just unstated.** The tier labels remain; the rule was assumed to be self-evident from the labels. Under this reading, the binding scope is still ~10 documents.
- **Reading B: The Compression Rule was retired without replacement.** All documents in all tiers are binding, with no priority distinction. Under this reading, the binding scope is ~24 documents (the Map's full list).

The recent project work appears to assume Reading B implicitly — the Operational Plan, the Compact, the Platform Adapter Contract, the Addenda, today's Tier 5 doctrine memo have all been treated as binding even though most of them would be Tier 3-5 under v1.4 conventions. But this assumption has not been formalized.

The implication for the audit: the binding-document list ranges from ~10 (Reading A) to ~34 (Reading B plus the unregistered documents from Finding 3). That is a 3.4x range in scope. Per-document audit is premature until the range collapses.

The reset memo must resolve which reading applies, and if Reading B, must explicitly retire the Compression Rule's logic in writing rather than by omission.

A third frame worth noting: **the Compression Rule's deletion may itself have been a mistake.** The v1.5 Map's simplification removed not only the Compression Rule but also the Canonical Declaration. Both removals leave the Map without explicit conflict-resolution logic. A document called "Documentation Map & Canonical References" with no canonical declaration has lost a load-bearing piece of itself. The reset memo may resolve that the right move is to *reinstate* the v1.4 conventions explicitly, with v1.5's structural improvements layered on top.

---

## 5. Finding 3 — Recently-authored documents bypass the Map entirely

Several documents I treated as binding in the gap audit's session brief are not registered in the Documentation Map v1.5 at all. They have been authored, committed, and operated against as binding without ever being indexed in the canonical index.

The unregistered set:

- **Platform & Writer's Room Compact v1.0** (April 2026) — operational compact between platform and Writer's Room components.
- **SquadVault Operational Plan v1.1** (April 2026) — the document defining Phases A through F and the operational tracks.
- **Platform Adapter Contract Card v1.0** — niche-agnosticism contract for platform adapters; this contract was the architectural backbone the recalibration arc cited.
- **Canonicalization Policy Addendum v1.0** and **Canonicalization Semantics Addendum v1.0** — addenda extending the canonicalization rules.
- **EAL Persistence Clarification Addendum v1.0** and **Editorial Attunement Layer — Core Engine Addendum v1** — addenda extending the EAL contract.
- **Weekly Recap Context Temporal Scoping Addendum v1.0** — addendum recently promoted from `_observations/` to `docs/addenda/` at `14c6003`.
- **Internal Note — Why The Editorial Attunement Layer Exists** — internal note, status-as-binding ambiguous.
- **Tier 5 Live Observation Cadence Doctrine v1.0** — shipped today at `1cf4142`. Postdates the Map. Not yet registered.

The pattern: documents authored after the v1.5 Map's last revision have not been added to the Map. The Map is itself out of date relative to the work product. This is a process-discipline finding: there is no Map-update step in the project's session-shipping discipline. New binding documents ship; the Map does not get touched.

The reset memo must resolve:

- Which of these unregistered documents are actually binding (vs. reference, vs. operational scaffolding)?
- What is the registration mechanism going forward such that future binding documents do not bypass the Map?
- Does the Map itself need a v1.6 that re-establishes the Compression Rule (or its replacement) and registers the currently-unregistered binding documents?

---

## 6. Implications for the reset arc — sequenced meta-questions

The reset memo session, when it runs, must resolve these meta-questions before per-document audit becomes meaningful:

**M1. Is the Compression Rule (or some equivalent priority distinction) still in effect?** Doctrine answer required, in writing, with explicit logic for how new binding documents register and how the project-day-to-day decides what to load as authority. Resolution shape: "Tier 0 through Tier X are binding; Tier X+1 through Tier 5 are reference-only, invoked explicitly." Or: "All documents in all tiers are binding, with conflict resolution by [explicit ordering]." Either is acceptable; ambiguity is not.

**M2. What is the Business Plan's authority status?** Pick one: binding-vision-source, reference-only, or retired. Document the rationale. If "binding-vision-source," carve out which sections bind (vision, founding intent) and which do not (growth projections, ARPU/CAC framework). If "retired," explain why the recalibration arc's treatment of it as binding-vision-source was an error and what the actual binding-vision-source is instead.

**M3. Which recently-authored documents are binding?** For each of the 8-10 unregistered documents identified in §5, doctrine answer: binding (and at which tier), reference-only, or operational-scaffolding-not-binding. Specifically including the Operational Plan v1.1, the Compact, the Platform Adapter Contract, the Tier 5 doctrine memo from today, and the Addenda.

**M4. What is the registration mechanism going forward?** When new binding documents ship, what session-discipline ensures the Map gets updated? This is a procedural question, not a doctrine question, but it follows from M1-M3 and prevents the same drift from recurring.

**M5. Does the Documentation Map need a v1.6?** If M1-M4 are resolved, the Map likely needs a revision to reflect them. The reset memo should commission the Map revision as a follow-on artifact, not author it inline.

These five questions are *sequenced*: M1 is the gating question (how do we know what's binding), M2 builds on M1 (where does the Business Plan fit), M3 builds on M1-M2 (where does the rest fit), M4 follows from M3 (process for additions), M5 follows from M1-M4 (Map revision).

The reset memo does not need to resolve all five in one session. M1-M3 are the substantive meta-questions; M4-M5 may defer to a successor session if the reset memo's session runs long.

---

## 7. Standing-backlog update

**Gap Audit (Document Reconciliation Audit v1.0)** — moved from active-work to *blocked-pending-meta-resolution*. The audit cannot proceed until the reset memo resolves M1 (binding-document scope) at minimum. Per-document audit is premature against a contested binding-document list.

**Reset Memo (Project Reset Memo v1.0)** — promoted to *active item #1* in the project reset arc. Its first scope item inherits M1-M5 from this closure memo. The reset memo's session brief, when authored, cites this closure memo as its evidentiary base.

**Documentation Map v1.6** — named as a conditional follow-on (gated on reset memo M1-M4 resolution).

**Standing backlog after this memo (re-ordered):**

1. **(NEW, ACTIVE)** Reset Memo v1.0 — predecessor: this closure memo. Inherits M1-M5.
2. **(BLOCKED)** Gap Audit Document Reconciliation v1.0 — blocked pending Reset Memo M1 resolution.
3. **(CONDITIONAL FOLLOW-ON)** Documentation Map v1.6 — gated on Reset Memo M1-M4.
4. (Carry-forward) Section 10 Q1 Bug 1 — DEFER at `50e3141`. Tier 5 monitors via doctrine §6.
5. (Carry-forward) SCORE_VERBATIM legacy-drift — CLOSED at `16d4a1b`. Tier 5 monitors via doctrine §6.
6. (Carry-forward) Player-streak verb inversion — named-only. Tier 5 monitors via doctrine §6.
7. (Carry-forward) Cat 3c row-76 W14 2025 attribution edge case — deferred. Tier 5 monitors via doctrine §6 manual prose inspection.
8. (Carry-forward) Snap-outcome detection — named-only. Tier 5 monitors via doctrine §6 manual prose inspection.
9. (Carry-forward) NOTABLE-pass alphabetical lockout investigation — named-only. Tier 5 monitors via doctrine §6 manual prose inspection.
10. (Carry-forward) Bug 1 classifier current-week scope extension — named-only. Promote-conditional on first real W14+ 2026 cycle revealing friction.
11. (Carry-forward) Tier 5 doctrine v1.1 — triggered by first real W14+ 2026 cycle that surfaces a refinement.
12. (Carry-forward) Framing B activation wrapper — deferred to follow-on session, gated on first real W14+ 2026 cycle.
13. (Carry-forward) Priority-list mechanism redesign — fifth-instance meta-item.

---

## 8. Methodology notes

**Closure-memo-for-halted-audit is a legitimate session artifact.** The brief committed today contemplated a partial-audit shipping path ("ship 60% of an audit cleanly than 100% under fatigue"). It did not contemplate a halted-at-meta-finding shipping path. The closure memo extends the partial-audit logic: if the audit halts at the meta-level, the closure memo captures the meta-findings rather than the per-document findings. The brief's "audit describes, doesn't synthesize" discipline still applies — the meta-questions M1-M5 are described, not resolved, in this memo.

**The Documentation Map is itself an audit-target rather than an audit-input.** This was unanticipated by the brief. The brief assumed the Map would produce the binding-document list; the Map produced four findings about its own contents and the conventions surrounding it. Future audit sessions should treat their list-source as audit-target-by-default, not audit-input-by-default.

**The Compression Rule's deletion in v1.5 is a methodologically important precedent.** When a document drops a load-bearing rule "in the name of simplification," the rule's absence may itself be a finding. Future doc-revision sessions should explicitly note rules that were considered for deletion and should require an accompanying memo for any rule actually deleted.

**Multi-frame deliberation surfaces the right shape.** The decision to halt the audit and produce a closure memo rather than power through was reached by deliberating among the process-engineering frame, the product-engineering frame, and the editorial frame, with explicit acknowledgment that they disagreed. The closure call (Option C in the deliberation) reflected the synthesis: the meta-question outranks the audit's discipline. Future similar moments should follow the same explicit-deliberation pattern.

**Bulletproof memo-write form per memory edit #21 was used for this memo.** Same quoted-delimiter heredoc plus raw-string body that landed today's earlier doctrine memo and session brief. Apply-then-verify discipline per memory edit #22 governs this commit's shipping. (The form itself is described abstractly here rather than illustrated literally; literal illustration would create the same paste hazard memory edit #21 was authored to avoid — a reflexive instance of the rule.)

---

## 9. Files and commits referenced

- `9a4fa89` — gap audit session brief commit (predecessor of this closure memo).
- `1cf4142` — Tier 5 live observation cadence doctrine v1.0.
- `_observations/session_brief_gap_audit.md` (`9a4fa89`) — the audit's session brief.
- `_observations/OBSERVATIONS_2026_05_07_TIER_5_LIVE_OBSERVATION_DOCTRINE.md` (`1cf4142`) — the prior session's doctrine memo.
- **Documentation Map v1.5** (project knowledge: `SquadVault_Documentation_Map_v1_5__1_.docx`) — current authoritative Map; subject of Findings 0-3.
- **Documentation Map v1.4** (project knowledge: `SquadVault_Documentation_Map_and_Canonical_References_v1_4_1.pdf`) — predecessor Map; comparison source for Finding 0.
- **SquadVault Business Plan** (uploaded 2026-05-07 via session conversation) — subject of Finding 1.
- `6740014` — Tests/ ruff cleanup non-finding closure (introduced closure-memo-for-non-findings as Norm 3).
- `14c6003` — Weekly Recap Context Temporal Scoping Addendum promotion (cited as evidence for Finding 3 unregistered-but-promoted-to-`docs/` pattern).
