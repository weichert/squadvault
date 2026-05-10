# OBSERVATIONS — Reset Memo v1.0 (project reset)

**Drafted:** 2026-05-07.
**HEAD at draft:** `6f55e00` (reset memo session brief commit).
**Phase:** 10 — Operational Observation; project reset arc.
**Position in plan:** Second substantive artifact of the project reset arc, after the gap-audit closure memo at `2dda2c2`. Resolves M1–M5 from that memo's §6 and formalizes the recalibration arc that ran during the 2026-05-07 session. Predecessor: `_observations/session_brief_reset_memo_v1_0.md` at `6f55e00`.

---

## 1. TL;DR

This memo formalizes the recalibration arc that ran during the 2026-05-07 session and resolves the five meta-questions (M1–M5) inherited from the gap-audit closure memo at `2dda2c2`. It is the second substantive artifact of the project reset arc, doc-only, single commit, predecessor `6f55e00`. The memo's content is binding doctrine; its filing in `_observations/` reflects v1.0 status with promotion to `docs/` gated on empirical validation by successor work.

**Recalibration arc (§2).** The Constitution's *integrity principles* — facts immutable, narratives derived, AI assists humans approve, silence over speculation, no analytics, no optimization, no engagement loops, no prediction — are binding and load-bearing under any scope. The Constitution's *scope restrictions* — single league, single tone, text-only, no frontend, no multi-modal, no discussion surface — were build-phase scaffolding for substrate work that is now complete; they are retired. The Business Plan is re-anchored as binding-vision-source. Niche-agnosticism is architecturally backed by clean import graph and platform-agnostic `canonical_events` schema. Phase 11 (Product Surface) is active.

**M1 (§3).** The Compression Rule and Canonical Declaration are reinstated verbatim as binding doctrine. *"Only Tier 0–2 documents should be loaded by default; Tier 3–5 are reference-only, invoked explicitly."* *"In the event of conflict, the Canonical Operating Constitution and subordinate Contract Cards take precedence."* The v1.5 Map's silent deletion of both rules is named as mistake. v1.5's structural improvements are preserved.

**M2 (§4).** The 2024 Business Plan binds in vision sections — the Founder's Letter, §3 paragraphs 1–2, §5 paragraphs 1–3, §6, and §7 — articulating SquadVault's destination as a digital clubhouse for fantasy football leagues built around legacy archival, league memory, and tone-modulated AI-assisted content generation. The growth-mechanics sections (§8, §11, §12, §13, §14, §17, §18, §19) and all 26 appendices are reference-only. The Constitution's integrity principles bind *how* the vision-tier features ship; vision authority is binding only as destination intent and is subordinate to Tier 0–2 doctrine on points of implementation conflict (§4.4 Authority subordination). Tone Engine modes permit stylistic extrapolation about events that occurred but not invented characterizations or speculative interpretations (§4.4 Tone Engine boundary). Social-memory surfaces are binding-vision; social-network mechanics (feeds, follower graphs, algorithmic resurfacing, engagement notifications) are forbidden regardless of how a surface is labeled (§4.4 Social-surface vs social-network).

**M3 (§5).** Ten unregistered binding documents are classified into the v1.4 tier structure. Operational Plan v1.1, the Compact, and the Tier 5 doctrine v1.0 are Tier 1 (operational, with the Tier 5 doctrine provisional). The Platform Adapter Contract and five addenda are Tier 2 (subordinate Contract Cards and addenda). The Internal Note is Tier 3 (reference). None are retired.

**M4 (§6).** Registration-as-commissioning is the doctrine: a binding document is not binding until registered in the Map. Authoring ships in two commits — the document, then the Map update. A pre-commit gate enforces this for `docs/` additions; the doctrine itself enforces it for `_observations/` provisional doctrine. The v1.6 Map is the bootstrap. The ten Finding-3 documents listed in §5 are granted binding status by curative ratification (§6.5) effective at this memo's commit; the amnesty applies only to the reset set and may not be invoked for documents authored after this memo.

**M5 (§7).** Documentation Map v1.6 is commissioned as a follow-on artifact. v1.6 reinstates the Compression Rule and Canonical Declaration in the index, registers the ten unregistered documents at the §5 tiers, reflects the Business Plan's binding-vision carve-outs, and codifies the registration-as-commissioning mechanism. Filing default `docs/SquadVault_Documentation_Map_v1_6.md`. Authoring is a separate session, not authored here.

**Phase 11 framing (§8).** Phase 11 ships under Apple-discipline: constraint over breadth, exquisite ship, per-surface constitutional memo, integrity inheritance, no new foundations. One or two surfaces shipped exquisitely, not five at minimum-viable. The Constitution's integrity principles bind every Phase 11 surface; the retired scope restrictions do not. Phase 12+ does not begin until a Phase 11 Closure Memo (§8.4) empirically certifies the Phase 11 outcome against six required certifications: surfaces shipped, integrity violations if any, qualitative league response, Apple-discipline assessment, growth-mechanics drift if any, and trust failures if any.

**Disruption-vs-artisan (§9).** The artisan frame is primary: an elegant product, built on the foundation of truth, served exquisitely to the founder's longtime league and to other leagues that find it. The disruption frame — viable business opportunity at scale — is a legitimate aspiration conditional on (a) the artisan frame succeeding first and (b) the integrity discipline scaling with the product. The Apple lineage is named explicitly, including its personal source. Empirical posture for engaging the disruption frame more substantively is deferred to a successor memo after Phase 11 surfaces ship.

**Standing backlog (§10).** The reset memo retires the M1–M5 backlog item. It commissions four new items (v1.6 Map authoring, pre-commit gate engineering, Phase 11 first-surface specification, the per-Phase-11-surface constitutional-memo framework) and unblocks the gap audit. Eight Tier-5-monitored carry-forward items are unchanged.

**What this memo does not do.** Does not author Map v1.6, the pre-commit gate, or any Phase 11 surface specification. Does not retire the Business Plan or any document classified reference-only. Does not retroactively invalidate prior session work that operated against the unregistered documents as binding. Does not commit Phase 12+ to either the artisan or disruption trajectory unconditionally; Phase 12+ requires the Phase 11 Closure Memo per §8.4, and the §9.2 artisan-primary stance governs the prioritization regardless of Phase 12+ trajectory.



---

## 2. The recalibration arc

### 2.1. The pre-recalibration state

Through 2026-05-06, the project operated against a strict-construction reading of the Canonical Operating Constitution that did not distinguish between two classes of restriction within that document. The Constitution names *integrity principles* — facts immutable and append-only, narratives derived never fact-creating, AI assists humans approve publication, silence over speculation, no analytics or optimization or engagement loops or prediction. It also names *scope restrictions* — single league, single tone, text output, no frontend, no multi-modal expansion, no discussion surface. Both classes are present in the document. Neither class was distinguished from the other in how the project's day-to-day reasoning treated them.

Under that reading, the project was approximately what the substrate work had built: a deterministic recap engine for one league, governed by integrity discipline, with the Constitution's scope restrictions binding for the indefinite future. Phase 10 was the active phase; Phase 11 was nominally next but unscoped. The Operational Plan v1.1 §10 was occasionally cited as forbidding multi-modal or social-surface expansion as Phase F+ work; the Business Plan §6, which lists multi-modal and social-surface as core feature set, was cited in tension. Both documents were treated as binding. Neither had formally retired the other.

This reading was not adopted in any single binding decision. It accumulated through repeated advisory work that conflated the two restriction classes, and through the absence of a forcing function that would have required the conflation to be examined.

### 2.2. The recalibration trigger

The recalibration arc began with a "where are we in the greater scheme" question raised during the 2026-05-07 session. The advisory framing in response to that question initially repeated the strict-construction reading: that the Constitution's scope restrictions were binding alongside its integrity principles, and that the multi-modal multi-tenant social-surface vision the Business Plan describes was deferred to an indefinite future phase or was implicitly retired by the Constitution's substance.

A subsequent turn surfaced the conflation. The Constitution's scope restrictions were not authored as permanent doctrine; they were authored as *build-phase scaffolding* — the boundaries on the substrate work that needed to complete before any expansion could be considered. The substrate work is now complete: the Implementation Excellence Plan (all seven phases) shipped at `b9f495c`; all four known defects resolved; test baseline at 1958 passed / 2 skipped; ruff and mypy clean. The scaffolding's purpose has been served.

The Constitution's *integrity principles*, by contrast, were authored as load-bearing doctrine. They constrain what kind of artifact SquadVault is regardless of scope. A multi-modal multi-tenant SquadVault that violates the integrity principles would not be SquadVault; a single-league text-only SquadVault that violates them would not be SquadVault either. The integrity tier is invariant under scope expansion.

### 2.3. The integrity-vs-scope distinction

The recalibration arc established the following distinction, which this memo formalizes as binding doctrine:

**Integrity principles are binding and load-bearing.** They include, at minimum: facts immutable and append-only; narratives derived from facts and never fact-creating; AI assists, humans approve publication; silence preferred over speculation; no analytics, no optimization, no engagement loops, no prediction. These principles bound every surface SquadVault has shipped, ships, or will ship. They are not relaxed under expansion; they are the discipline that lets expansion proceed without becoming the thing the discipline was meant to prevent.

**Scope restrictions were build-phase scaffolding and are retired.** They included: single league only; single tone only; text output only; no frontend; no multi-modal expansion; no discussion surface; no cross-league features. These were boundaries on the substrate work. With the substrate complete, the scaffolding is removed. Phase 11 and beyond may legitimately introduce new tones, new modalities, new tenants, new surfaces — subject to the integrity principles, never subject to the retired scaffolding.

This is not a relaxation of doctrine. This memo authoritatively interprets the Constitution's prior scope restrictions as build-phase constraints rather than permanent integrity constraints. The Constitution's text is unchanged; the binding interpretation it carries is updated by this memo. Future contributors should read this section, not the bare Constitution, as the source of how the scope restrictions are now understood.

### 2.4. The Business Plan re-anchored

The SquadVault Business Plan, dated 2024 per its own framing, articulates the multi-modal multi-tenant social-surface vision that Phases 11 and beyond will pursue. The Founder's Letter, §3 (Vision & Why Now), and §6 (Core Features & Functionality) describe the destination the substrate work has been building toward. The Documentation Map v1.5 omits the Business Plan from any tier; the Map v1.4 listed it as Tier 5 (archival). Neither classification matches the role the recalibration arc identified.

This memo's §4 (M2 resolution) deliberates the Business Plan's per-§ authority status — which sections bind and which do not. Pending that resolution, the recalibration arc treats the Business Plan as **binding-vision-source**: the document whose original ambition is honored by Phase 11+ work, with specific carve-outs to be settled in §4.

The recalibration's framing of the Business Plan is not adoption of its growth mechanics — ARPU, CAC, Year-3 revenue projections, churn modeling. Those sections read as venture-pitch artifact rather than binding doctrine, and §4 likely settles them as such. The recalibration's framing is adoption of the Business Plan's *vision*: that SquadVault is, in its full form, a multi-modal multi-tenant social platform for league memory, and the substrate is the foundation that lets the full form ship without violating the integrity principles.

### 2.5. Niche-agnosticism, architecturally backed

The recalibration arc surfaced a question — whether the substrate's tight binding to fantasy football and to the MFL platform constituted a doctrinal commitment or a contingent implementation detail. An architectural inspection produced empirical evidence:

- The `core/` import graph is clean of `mfl/` and `recaps/writing_room/` — `core/` does not depend on platform-specific or niche-specific modules.
- The `canonical_events` schema is platform-agnostic — its fields are general (event_type, payload, timestamps, source_id) rather than fantasy-football-specific.
- The Platform Adapter Contract Card v1.0 names niche-agnosticism as an explicit architectural commitment.
- Fantasy-football-specific surface inside `core/` is bounded and relocatable, estimated at ~10–15% of `core/`'s volume.

The substrate is therefore niche-agnostic in design and substantially niche-agnostic in implementation. The fantasy football binding is not a doctrinal commitment; it is the niche the first surface ships against. Phase 11+ may legitimately introduce other niches, subject to the integrity principles and to architectural work that completes the platform-agnostic refactor where it is incomplete.

### 2.6. Phase 11 active; Phases 12+ contemplate the full vision

Phase 10 (Operational Observation) remains active for the in-flight 2025 season processing. Phase 11 (Product Surface) is now also active and is the active phase for new development work. Phase 11's substantive surface is not specified by this memo; surface specification happens in successor sessions, each Phase 11 surface receiving its own constitutional memo per the discipline §8 of this memo names.

Phases 12+ contemplate the larger Business Plan vision: multi-modal expansion (audio, video, image-rich recap surfaces), multi-tenancy (multiple leagues with isolation), social-surface elements (Hall of Fame & Shame, league chat replays, the locker room and the memory bank in one), the multi-tone Tone Engine. None of these are scoped here; the memo names that they exist in the project's binding-vision horizon, and the integrity principles bound them.

### 2.7. What the recalibration is not

The recalibration is not adoption of growth-mechanics framings — engagement loops, retention metrics, network effects as success criteria, scale-as-virtue. The Business Plan's growth-mechanics sections are, in §4's likely resolution, not binding. The integrity principles' explicit prohibition of analytics, optimization, engagement loops, and prediction is unchanged and binding regardless of scope expansion.

The recalibration is not retirement of the Constitution. The Constitution remains the source-of-truth for integrity principles. What was retired was a reading of the Constitution that conflated build-phase scaffolding with load-bearing doctrine.

The recalibration is not a pivot. The substrate's first shipping surface, PFL Buddies recap generation for the 2025 season, remains the immediate operational concern. Phase 10 work continues. Phase 11 work begins in parallel. The recalibration changes the framing within which both phases proceed.

---

## 3. M1 — Compression Rule status: reinstate v1.4 conventions explicitly with v1.5's structural improvements layered on top

**Resolution.** The Compression Rule and the Canonical Declaration are reinstated as binding doctrine. Their deletion from the Documentation Map v1.5 is named here as a mistake — the v1.5 simplification removed two load-bearing rules without replacement, and the project has been operating without canonical conflict-resolution logic since. The structural improvements in v1.5 (registration of Selection Set Schema and Rivalry Chronicle as Tier 2; the Conceptual Components section naming Social Layer as deferred) are preserved.

### 3.1. The Compression Rule, reinstated verbatim

> Only Tier 0–2 documents should be loaded by default during design, development, or AI-assisted reasoning. Tier 3–5 documents are reference-only and must not be treated as authority unless explicitly invoked.

This rule is binding. It governs how every session, every advisory turn, and every doctrine-reasoning episode decides what counts as authority. The default-loaded set is Tier 0–2; Tier 3–5 documents are consulted under explicit invocation, with the invocation itself recorded in the session's artifacts.

### 3.2. The Canonical Declaration, reinstated verbatim

> In the event of conflict, the Canonical Operating Constitution and subordinate Contract Cards take precedence.

This declaration is binding. It is the conflict-resolution rule the v1.5 Map's silent retirement left the project without. Where two binding documents disagree, the Canonical Operating Constitution and its subordinate Contract Cards win; other binding documents (operational plans, compacts, addenda) yield to the Constitution and Contract Cards on points of conflict.

### 3.3. Why this resolution

Three readings of M1 were considered: (A) the Compression Rule still applies, just unstated; (B) the Compression Rule was retired without replacement; (C) reinstate v1.4 conventions explicitly, with v1.5's structural improvements layered on top.

Reading A is too narrow. It keeps a binding scope of ~10 documents and offers no elevation path for documents the project has demonstrably needed to treat as binding — the Operational Plan v1.1, the Platform & Writer's Room Compact, the Platform Adapter Contract, the Canonicalization Addenda, the EAL Addenda, the Temporal Scoping Addendum, the Tier 5 doctrine. Under Reading A, the project would have to either re-classify these as reference-only (which contradicts how the project has actually been operating) or treat them as silently-elevated to binding (which is the same drift Reading A was supposed to correct).

Reading B is too flat. It preserves the project's recent practice of treating all documents as binding, but does so by dissolving the priority distinction that governance documents need. With 30+ binding documents and no conflict-resolution rule, the project loses the ability to say *the Constitution wins* when an operational document drifts away from constitutional discipline — which is exactly the kind of drift the v1.5 Map's deletion of the Canonical Declaration enabled. Reading B's flatness is what made the project's silent adoption of growth-mechanics framings advisable rather than alarming, and why the recalibration arc earlier this session was needed.

Reading C accommodates the project's actual practice without dissolving doctrine into flatness. The Operational Plan v1.1 and Compact are not Tier 5 under v1.4 conventions; under correct classification they are Tier 1 or Tier 2 operational doctrine. The fix is not to retire the Compression Rule but to *correctly classify* the recent documents within it — which is the M3 work in §5 of this memo. The Canonical Declaration's reinstatement gives the project the conflict-resolution logic Reading B lacks; the structural improvements from v1.5 are preserved.

### 3.4. The v1.5 deletions, named as mistakes

The Documentation Map v1.5 deleted both the Compression Rule and the Canonical Declaration without accompanying memo or commit-message rationale. This memo names both deletions as mistakes. The deletions removed load-bearing rules from a document whose purpose is to be the canonical index, and they did so silently — the kind of governance drift the project's discipline is supposed to prevent.

This is not a recrimination. The v1.5 simplification likely reflected a sincere attempt to reduce the Map's friction; it produced an unintended consequence that this memo corrects. Documentation Map v1.6, commissioned in §7 of this memo (M5), reinstates both rules in writing, registers the unregistered binding documents (M3), and reflects the structural improvements v1.5 introduced. v1.6 is the operational artifact; this memo is the doctrine that v1.6 implements.

### 3.5. Operational consequences

Three immediate consequences of reinstating the Compression Rule:

**Default load set.** Sessions, advisory turns, and AI-assisted reasoning episodes default to Tier 0–2 documents as authority. Tier 3–5 documents are consulted under explicit invocation, named in the session's artifacts. The "default" here is not a hard restriction; it is the discipline that governs what counts as binding when no specific invocation is made.

**Tier classifications matter.** Which tier a document sits in is no longer cosmetic. Documents currently mis-classified — in particular the unregistered documents from Finding 3 — must be classified correctly in v1.6. The M3 work in §5 of this memo settles each.

**Reference is not retirement.** A document classified as Tier 3–5 (reference-only) is not retired or invalidated; it is available for explicit invocation when its substance is relevant. The Compression Rule's intent is to prevent unintentional binding-by-citation, not to render reference documents useless.

Three immediate consequences of reinstating the Canonical Declaration:

**Conflict resolution is non-democratic.** When binding documents disagree, the Constitution and its subordinate Contract Cards win. Operational plans, compacts, and addenda yield to the Constitution on points of substantive conflict. Where the conflict is ambiguous (the documents are readable as compatible under charitable interpretation), the Canonical Declaration is silent — charitable interpretation is the first move; explicit conflict resolution is the fallback.

**The Constitution's integrity principles are explicitly defended.** The recalibration arc in §2 established the integrity-principles tier as binding regardless of scope. The Canonical Declaration is the procedural mechanism that defends that tier against drift. If a future operational doctrine introduces engagement-loop framings, prediction features, or analytics-as-success-criteria, the Canonical Declaration is the rule that says: the Constitution wins.

**Subordinate Contract Cards inherit the precedence.** The Platform Adapter Contract, the Selection Set Schema, the Rivalry Chronicle Contract Card, the FAAB Outcome Insight Contract Card, the Creative Layer Contract Card — Tier 2 contract cards are subordinate to the Constitution and inherit its precedence over Tier 1 operational documents. Operational plan revisions cannot silently relax contract-card commitments.

### 3.6. Linkage to M3 and M5

§3 commits the project to M3 and M5 substantively. The reinstated Compression Rule operates against the registered binding-document list, and the registered list is currently incomplete (Finding 3 of `2dda2c2`). M3 in §5 of this memo classifies each unregistered document; M5 in §7 commissions Documentation Map v1.6 as the operational artifact that reflects the M3 classifications and reinstates the Compression Rule and Canonical Declaration in the index itself.

Until v1.6 ships, this memo's §5 is the authoritative classification source. Sessions operating between this memo's commit and v1.6's commit defer to §5 for binding-status questions on the Finding 3 documents. v1.6's authoring session is conditional on M4 (registration mechanism) resolution.


---

## 4. M2 — Business Plan authority: binding-vision-source with per-§ carve-outs

**Resolution.** The SquadVault Business Plan (2024) binds in its vision sections — the Founder's Letter, §3 paragraphs 1–2, §5 paragraphs 1–3, §6, and §7. These sections articulate the destination Phase 11+ pursues: a digital clubhouse for fantasy football leagues built around legacy archival, league memory, and tone-modulated AI-assisted content generation. The growth-mechanics sections (§8 Market Analysis, §11 Business & Revenue Model, §12 Go-To-Market, §13 Marketing Plan, §14 Sales Strategy, §17 Financial Overview, §18 Marketing Strategy, §19 Sales & Revenue Model) and all 26 appendices (A1–A26) are reference-only — not retired, available for explicit invocation when their substance is relevant, but not binding doctrine. The Constitution's integrity principles bind *how* the vision-tier features and capabilities ship.

### 4.1. Why this resolution

Three frames were considered, drawn from the closure memo's §3 articulation: venture-pitch artifact (never binding); binding-vision-source; superseded by later doctrine.

**Reading A — venture-pitch artifact** discards too much. The Business Plan opens "Prepared for prospective investors and strategic partners" and the growth-mechanics sections do read as venture-pitch artifact — ARPU $15/month, CAC $12, churn 10% annually, Year 1–3 revenue projections targeting 8,000 paying leagues, sponsored integrations, brand partnerships. Were the Business Plan binding in those sections, the project would have implicitly committed to revenue targets and engagement-optimization framings the recalibration arc explicitly retired. The recalibration's clarity about scope-restriction retirement does not extend to growth-mechanics adoption. So far, Reading A is correctly diagnosing the threat. But Reading A then over-corrects by discarding the Founder's Letter and §3 and §6 — sections that articulate what SquadVault is *for* in language that no later document carries. The Founder's Letter's "more than an app... a digital clubhouse... the locker room and the memory bank in one" is vision-doctrine; nothing in the Constitution, Compact, or Operational Plan articulates this. Reading A leaves the project without a vision-doctrine.

**Reading C — superseded** has a similar failure mode. The Constitution constrains; it doesn't aspire. The Compact bounds niche-agnosticism; it doesn't articulate destination. The Operational Plan describes operational tracks; it doesn't name the digital clubhouse. None of the post-2024 documents articulates the vision-destination. Reading C therefore commits the project to vision-doctrine homelessness, recoverable only by authoring a new vision-doctrine — which is a separate session, separate artifact, and separately settled doctrine. The cost-of-recovery is high; the benefit (cleaner Map omission) is low.

**Reading B — binding-vision-source with per-§ carve-outs** accommodates the project's actual practice. The recalibration arc's framing of the Business Plan as "the document whose original ambition is honored by Phase 11+ work" is supported by close reading. The Founder's Letter and §3 vision-paragraphs and §6 feature-list are vision-substantive. The growth-mechanics sections are not. The carve-out work is real but tractable — paragraph-level distinctions where needed (§3 and §5), section-level where the section is uniformly one shape (§6 binding, §11 reference). Reading B requires that the integrity principles be explicit about what they bind: not just *that* features ship, but *how* features ship.

### 4.2. The binding-vision tier (per-§ classification)

The following Business Plan sections are binding doctrine in their vision-substantive content. Each section's binding scope is named explicitly; paragraph-level distinctions are made where the section's prose mixes vision-substance with venture-pitch rhetoric.

**Founder's Letter — entire section, binding.** The most load-bearing single piece of vision-doctrine in the document. Articulates SquadVault's purpose ("more than an app... a digital clubhouse... the locker room, the group chat, the postgame barstool, and the memory bank in one") and the founding intent ("born from friendships... an emotional anchor through life's triumphs and challenges"). The Founder's Letter binds for what it says SquadVault is *for*.

**§3 Vision & Why Now — paragraphs 1–2, binding.** The "Our Vision" framing ("emotional engine behind every fantasy football league... legacy-preserving social layer for the millions who log in each fall to feel connected") is vision-substantive and binding. Paragraphs 3–5 (the "Why Now? Three converging trends" articulation — Social Gaming Surge, Fantasy League Saturation, AI + Personalization) are investor-timing rhetoric and not binding. The trends may or may not have aged accurately; the vision they were marshalled to justify binds independent of them.

**§5 Product & Technology Overview — paragraphs 1–3, binding.** The Memory Engine / Tone Engine / Vault Architecture framing is binding-vision-substantive. The Memory Engine binds the project to auto-generated league histories, power rankings, milestone alerts, and legacy awards as destination capabilities. The Tone Engine binds the project to tone-modulated content generation. The Vault Architecture binds the project to long-term archival of league data, inside jokes, media, and moments. Paragraphs 4–6 (the React.js / Python / AWS / MongoDB tech-stack details, the cross-app extensibility discussion with Inbox Assassin) are implementation-detail and not binding doctrine — the substrate may or may not match these specific stack choices, and the binding is on the architectural shape, not the implementation choices.

**§6 Core Features & Functionality — entire section, binding.** The legacy-archival features (Draft History Vault, Championship Timeline, Hall of Fame & Shame), AI-enhanced communication tools (Weekly Recap Generator, Commissioner Toolkit, Media Packs), and personal vaults & social extensions (Quote Capture, Media Wall, League Chat Replays) are all binding-vision-substantive. The substrate's PFL Buddies recap generation is the first shipping instance of the Weekly Recap Generator capability §6 names; future Phase 11+ work pursues the rest. Subject to the integrity-principles-bind-how-features-ship clause in §4.4 below.

**§7 Tone Engine: Differentiator & IP — entire section, binding.** Multi-tone generation (Roast Mode / Hype Mode / Emotional Mode / Analyst Mode), proprietary fine-tuned AI, league-culture-aware content generation. The Tone Engine is the project's signature differentiator and its multi-tone nature is binding-vision. The substrate's current single-tone implementation is the first surface; multi-tone expansion is in the Phase 11+ horizon. Subject to the integrity-principles binding clause.

### 4.3. The reference-only tier

The following Business Plan sections and all 26 appendices are reference-only — available for explicit invocation when their substance is relevant, not binding doctrine. Their content does not retire under this classification; their *authority status* is reference. The project may consult them for context, may cite them in operational discussions, may draw on them for surface-specification — but the project does not commit to them as binding goals or as binding constraints.

- **§4 Problem & Opportunity** — investor-facing problem articulation. Useful for understanding the project's framing context. Not binding.
- **§8 Market Analysis & Trends** — venture-pitch market sizing. Reference.
- **§9 Target Customer Profiles** — venture-pitch persona articulation. Reference.
- **§10 Competitive Landscape** — venture-pitch competitive positioning. Reference.
- **§11 Business & Revenue Model** — Free/Pro/Enterprise tier structure, sponsored integrations, ad embedding framings, "scalable, sticky" rhetoric. **Explicitly not binding.** The integrity principles' prohibition of analytics, optimization, engagement loops, and prediction takes precedence over §11's growth-mechanics framings; where §11 implies engagement-optimization as a binding goal, it does not.
- **§12 Go-To-Market Strategy** — venture-pitch launch strategy. Reference.
- **§13 Marketing Plan** — venture-pitch. Reference.
- **§14 Sales Strategy** — venture-pitch. Reference.
- **§15 Customer Support & Community Engagement** — operational reference.
- **§16 Competitive Analysis** — venture-pitch. Reference.
- **§17 Financial Overview** — ARPU $15/month, CAC $12, churn 10%, Year 1–3 revenue projections, break-even at 1,800 paying leagues. **Explicitly not binding.** The project has not committed to these targets and the integrity principles prohibit treating them as binding goals.
- **§18 Marketing Strategy** — venture-pitch. Reference.
- **§19 Sales & Revenue Model** — venture-pitch. Reference.
- **§20–§22** — operational/historical reference (legal/risk; milestones; team).
- **§23 Team & Advisors** — historical reference.
- **§24 Risks & Mitigations** — operational reference.
- **§25 Appendix and all 26 Appendices A1–A26** — reference. The appendices include legal-structure planning (A20, Delaware C-Corporation framing for venture investment), Investor FAQ (A21, which describes SquadVault as "designed to maximize engagement and camaraderie" — engagement-optimization vocabulary the integrity principles forbid as binding), user personas, competitive feature matrices, sponsor targets, team biographies, visual asset indexes. None are binding.

### 4.4. The integrity-principles binding clause

The Business Plan's vision sections describe destination *features* and destination *capabilities*. The Constitution's integrity principles bind *how* those features and capabilities ship.

This clause is the synthesis move that makes Reading B coherent. Without it, the Business Plan's vision sections — specifically §6 and §7 — could be read as committing the project to features whose natural implementations would violate the integrity principles. With it, the binding distinguishes between *what* the project builds (vision-tier) and *how* it builds it (integrity-tier).

Examples of how this clause operates in practice:

- **Hall of Fame & Shame** as league-memory archive of what actually happened is binding-vision. Hall of Fame & Shame as engagement-optimization mechanism — surfaced to drive return visits, gamified to maximize sharing, optimized for retention — is not. The feature ships subject to silence-over-speculation: members are honored or lampooned for events that occurred; speculation about events that did not occur is forbidden.
- **Weekly Recap Generator** as humans-approve AI-assists publication is binding-vision. Weekly Recap Generator as autonomous publication is not. The substrate's current humans-approve discipline is the binding implementation pattern; full autonomy is forbidden by the AI-assists-humans-approve integrity principle.
- **Tone Engine multi-tone generation** as governed expressive output is binding-vision. Tone Engine as engagement-loop driver — tones selected to maximize emotional response, content tuned to drive sharing or retention — is not. Tone selection ships subject to facts-immutable: the recap's tone may vary; the recap's facts may not.
- **League Chat Replays** as faithful archival of past communications is binding-vision. League Chat Replays as engagement surface — surfacing controversial threads to drive return visits, recommending threads optimized for emotional response — is not. Faithful archival of what was said; no recommender, no optimization, no prediction of which threads to surface.

**Tone Engine boundary clause.** The Tone Engine's stylistic modes (Roast, Hype, Emotional, Analyst) require LLMs to extrapolate, exaggerate, and synthesize. This is in tension with the silence-over-speculation principle. The boundary: Tone Engine tones permit *stylistic extrapolation about events that occurred* — varying the tone, rhythm, vocabulary, and emotional register of a recap whose factual claims are verified. Tone Engine tones do not permit (a) invented characterizations attributed to specific individuals (e.g., "Team A's manager said X" when no such statement was made), (b) invented historical claims (e.g., "this is the worst loss in league history" when not verified against the canonical event ledger), (c) speculative interpretations attributed as facts (e.g., "Team A clearly didn't read the waiver wire" when the manager's actual reasoning is unknown), or (d) emotional manipulation engineered to drive specific user response (the integrity principle's prohibition of optimization applies). Tone varies; facts do not; speculation about motive, intent, or counterfactual outcome is not factual.

**Social-surface vs social-network distinction.** The Business Plan's vision-tier features (Hall of Fame & Shame, League Chat Replays, Personal Vaults, the digital-clubhouse framing) are *social-memory surfaces* — shared archives of what happened, human-curated publication, retrospective storytelling, group-owned memory. They are not *social-network mechanics* — feeds, follower graphs, likes-as-optimization-signals, algorithmic resurfacing, engagement notifications, recommended-controversy loops, "people are talking about" surfaces. The distinction is binding: any Phase 11+ surface that introduces social-network mechanics violates the integrity-tier prohibitions on engagement loops, optimization, and prediction, regardless of how the surface is labeled. The phrase "digital clubhouse" describes social-memory; it does not authorize social-network drift.

The integrity principles are not a side-constraint on the vision; they are the discipline that makes the vision shippable as SquadVault rather than as the engagement-optimized facsimile a strict-reading of §6 alone could justify. Phase 11+ surfaces inherit this clause.

**Authority subordination.** "Binding-vision-source" authority is binding only as destination intent — what the project commits to building toward. It is never binding as implementation authority. Where the Business Plan's vision sections appear to specify implementation, design, or operational choices that conflict with Tier 0 (Constitution-tier integrity), Tier 1 (operational doctrine), or Tier 2 (subordinate Contract Cards and addenda), the Tier 0–2 doctrine wins. Subordination order in summary: Constitution and integrity principles first; subordinate Contract Cards second; operational doctrine and addenda third; binding-vision-source subordinate to all three on points of substantive conflict. The vision tells the project where it is going; the lower tiers tell the project how it gets there.

### 4.5. Caveats and the recalibration arc's role

Two honest caveats on this resolution.

First, the recalibration arc that ran during the 2026-05-07 session pre-named binding-vision-source as the resolution. M2's deliberation in this memo therefore had a thumb on the scale before the deliberation started. The Business Plan re-read during this memo's authoring session supports Reading B more cleanly than A or C, and the carve-out boundary is in fact drawable at the §-level and paragraph-level the resolution names — but the prior pre-naming should be acknowledged. A future contributor reading this resolution should not infer that the deliberation was de novo; it was, in part, ratification of a recalibration the project had already committed to.

Second, the §3 and §5 paragraph-level carve-outs are fine-grained. A coarser §-level resolution ("§3 binds entirely" or "§3 doesn't bind") would be simpler to maintain. The fine-grained resolution is more honest to the document's actual prose — §3 paragraphs 1–2 are vision; paragraphs 3–5 are investor-timing rhetoric — but it requires that future contributors honor the paragraph-level boundary. The memo's resolution adopts the fine-grained boundary explicitly to avoid the ambiguity a coarser resolution would carry.

### 4.6. Linkage to §5 (M3)

§4 commits the project to a vision-tier classification for the Business Plan. §5 (M3) classifies the recently-authored binding documents — Operational Plan v1.1, Compact, Platform Adapter Contract, the Addenda, the Tier 5 doctrine, the Internal Note. The framework §4 establishes — that vision-tier doctrine articulates *what* and integrity-tier doctrine binds *how*, with operational-tier doctrine sitting between them — is the framework §5 operates against.

Specifically: §5 will classify each unregistered document as Tier 0 (Constitution-tier integrity), Tier 1 (operational-doctrine), Tier 2 (subordinate Contract Card), or Tier 3+ (reference). The Business Plan's vision sections do not fit cleanly in this tier structure (they precede it) and require their own treatment, which §4 has provided. v1.6 of the Documentation Map (commissioned in §7) reflects both the M3 classifications and the Business Plan's special-case binding-vision tier.


---

## 5. M3 — Recently-authored binding documents: per-document tier classification

**Resolution.** Ten unregistered documents are classified into the v1.4 tier structure as binding doctrine at Tier 1 (operational), Tier 2 (subordinate Contract Card or addendum), or Tier 3 (reference). None are retired. The classifications operate against the Compression Rule reinstated in §3.1: Tier 0–2 documents are binding; Tier 3 documents are reference-only and consulted under explicit invocation. The Documentation Map v1.6 commissioned in §7 reflects these classifications in the index itself.

The Constitution remains the sole occupant of Tier 0. The Compact between platform and Writer's Room, the Operational Plan v1.1, and the Tier 5 doctrine are operational doctrine at Tier 1. Contract Cards and addenda are at Tier 2. The Internal Note explaining the EAL is reference at Tier 3.

### 5.1. Per-document classifications

The classifications below adopt the v1.4 tier vocabulary: Tier 0 (Constitution-tier integrity), Tier 1 (operational doctrine), Tier 2 (subordinate Contract Cards and addenda), Tier 3 (archival reference, consulted under explicit invocation per §3.1). Tiers 4–5 from v1.4 are preserved structurally but no unregistered document falls into them.

**1. SquadVault Operational Plan v1.1** (April 2026) — **Tier 1 (operational doctrine).** Defines Phases A through F and the operational tracks the project runs under. Most load-bearing of the unregistered documents in the operational tier; binding for how the project sequences work and decides what's in-scope per phase. Subordinate to the Constitution per the Canonical Declaration in §3.2.

**2. Platform & Writer's Room Compact v1.0** (April 2026) — **Tier 1 (operational doctrine).** Bounds the platform/Writer's Room boundary and articulates the niche-agnosticism architectural commitment that the recalibration arc cited as architecturally backed (§2.5). Could be argued as Tier 2 contract-card-shaped, but its scope governs the relationship between two large architectural domains rather than a single interface; Tier 1 is the correct slot. The Compact's niche-agnosticism claim is binding; the Phase 11+ work in §8 honors it.

**3. Platform Adapter Contract Card v1.0** — **Tier 2 (subordinate Contract Card).** Specifies the niche-agnosticism interface that platform adapters must honor. Contract-card-shaped by construction; subordinate to the Constitution per the Canonical Declaration. The MFL adapter is the first surface implementing this contract; future adapters (other fantasy platforms, other niches per §2.5) honor the same contract.

**4. Canonicalization Policy Addendum v1.0** — **Tier 2 (subordinate addendum).** Extends the canonicalization rules. Integrity-adjacent — bears on the facts-immutable principle by governing how facts are canonicalized — but addendum-shaped rather than constitutive; subordinate to the Constitution-tier integrity principles it extends.

**5. Canonicalization Semantics Addendum v1.0** — **Tier 2 (subordinate addendum).** Pair with #4. Same shape; same subordination.

**6. EAL Persistence Clarification Addendum v1.0** — **Tier 2 (subordinate addendum).** Addendum to the Editorial Attunement Layer contract, which is itself Tier 2; the addendum is subordinate-extension at the same tier.

**7. Editorial Attunement Layer — Core Engine Addendum v1** — **Tier 2 (subordinate addendum).** Pair with #6. Same shape; same subordination. Note: the project knowledge contains a separately-named "Core Engine Specification — Editorial Attunement Layer Crossreference v1" document; per session-time confirmation, this is a duplicate of #7 and not a substantively distinct artifact. If a future audit identifies the cross-reference document as substantively distinct, M3 in a successor reset memo can re-classify.

**8. Weekly Recap Context Temporal Scoping Addendum v1.0** — **Tier 2 (subordinate addendum).** Promoted from `_observations/` to `docs/addenda/` at `14c6003`. Extends temporal-scoping rules for league-history loaders. Subordinate-extension at Tier 2; the promotion to `docs/addenda/` is the precedent §6 (M4) below names for the registration mechanism.

**9. Internal Note — Why The Editorial Attunement Layer Exists** — **Tier 3 (reference).** Explains *why* the EAL contract exists rather than constituting binding doctrine. Internal notes that aid understanding of binding documents are reference-shaped by construction. The EAL contract (#7) binds; the note explaining it is reference. Available for explicit invocation when the EAL contract's rationale is the question at hand.

**10. Tier 5 Live Observation Cadence Doctrine v1.0** (`1cf4142`) — **Tier 1 (operational doctrine), provisional.** Authored as v1.0 with explicit promotion-to-`docs/` path gated on empirical validation by one or two real W14+ 2026 cycles. The provisional status is captured by the doctrine's filing in `_observations/` rather than `docs/`; the binding-status is Tier 1 — it governs how Tier 5 cycles operate, what their re-activation criteria are, and how their toolkit is exercised. Promotion to `docs/50_ops_and_build/` upon empirical validation does not change the tier; it changes the durability of the filing location.

### 5.2. Summary table

| # | Document | Tier | Notes |
|---|----------|------|-------|
| 1 | SquadVault Operational Plan v1.1 | Tier 1 | Operational; most load-bearing of the unregistered set. |
| 2 | Platform & Writer's Room Compact v1.0 | Tier 1 | Operational; niche-agnosticism architectural commitment. |
| 3 | Platform Adapter Contract Card v1.0 | Tier 2 | Subordinate Contract Card. |
| 4 | Canonicalization Policy Addendum v1.0 | Tier 2 | Subordinate addendum. |
| 5 | Canonicalization Semantics Addendum v1.0 | Tier 2 | Subordinate addendum. |
| 6 | EAL Persistence Clarification Addendum v1.0 | Tier 2 | Subordinate addendum. |
| 7 | EAL — Core Engine Addendum v1 | Tier 2 | Subordinate addendum. |
| 8 | Weekly Recap Context Temporal Scoping Addendum v1.0 | Tier 2 | Subordinate addendum; promoted to `docs/addenda/` at `14c6003`. |
| 9 | Internal Note — Why The EAL Exists | Tier 3 | Reference; explains binding doctrine, does not constitute it. |
| 10 | Tier 5 Live Observation Cadence Doctrine v1.0 | Tier 1 | Operational, provisional; filing in `_observations/` reflects provisional status. |

### 5.3. What this resolution does and does not do

**What it does.** Establishes the binding-status of each unregistered document explicitly. Removes the ambiguity that allowed several of these documents (notably the Operational Plan v1.1 and the Compact) to be treated as binding without formal registration. Provides the substrate for Documentation Map v1.6 (commissioned in §7) to register them in the canonical index. Until v1.6 ships, this section is the authoritative classification source per §3.6.

**What it does not do.** Does not retire any document. Does not change the document-content of any. Does not retroactively invalidate prior session work that operated against these documents as binding — the documents *were* binding under the project's de facto practice; M3 formalizes what the practice already was, with the Internal Note as the one exception (it was treated as ambiguous and is now classified reference). Does not author the v1.6 Map; that authoring is commissioned in §7 as a follow-on artifact.

**A note on the Compact's tier placement.** The Compact (#2) was placed at Tier 1 rather than Tier 2 because its scope is broader than a single contract-card interface. A future audit may revisit this — the Compact's niche-agnosticism articulation has Contract-Card-tier characteristics — and a reset memo successor or v1.6 Map authoring session may reclassify if the project's evolving practice argues for Tier 2. The current Tier 1 placement reflects the Compact's load-bearing scope, not a final judgment on its taxonomy.

### 5.4. Linkage to §6 (M4) and §7 (M5)

§5 commits the project to a per-document classification that v1.6 of the Documentation Map will reflect. §6 (M4) addresses the *registration mechanism* — the session-discipline that ensures future binding documents do not bypass the Map the way these ten did. §7 (M5) commissions v1.6 itself.

The classification work in §5 makes M4 and M5 actionable. M4's registration mechanism operates against a known classification framework; M5's v1.6 has a known list of unregistered documents to register. Without §5, both M4 and M5 would be exercises in abstract process design; with §5, they are concrete next steps.


---

## 6. M4 — Registration mechanism: registration-as-commissioning, with pre-commit enforcement for `docs/`

**Resolution.** A binding document is not binding *until* it is registered in the Documentation Map. Authoring a binding doctrine ships in two commits: the document itself, then the Map update that registers it. Until the registering commit lands, the document is provisional — operational and consultable but not authoritative. A pre-commit gate enforces this for additions under `docs/`; the doctrine itself enforces it for `_observations/` provisional doctrine. The v1.6 Map is the bootstrap: registration of all currently-unregistered binding documents (per §5) ships in the same authoring act that establishes the registration mechanism going forward.

### 6.1. Why this resolution

Four candidate mechanisms were considered:

**Mechanism A — Map-update step in session-completion checklist.** Honor system. Every session that ships a new binding document includes a Map-update step. Rejected: honor systems for documentation discipline have failed five times in this project (the closure memo's five-instance stale-backlog pattern). Doctrine-by-aspiration is what produced Finding 3.

**Mechanism B — Pre-commit gate detecting `docs/` additions without Map modification.** Mechanical enforcement. Rejected as sole mechanism: the gate catches new top-level `docs/` documents but misses `_observations/` doctrine that postdates the Map (the Tier 5 doctrine at `1cf4142` is the canonical example). Extending the gate to cover `_observations/` would be too aggressive — the directory legitimately contains non-binding observation memos. Useful as supporting enforcement for the `docs/` case.

**Mechanism C — Quarterly Map-review cadence.** Standing review every N sessions or every quarter. Rejected: accumulating ~10–20 sessions of work between reviews is the accumulation pattern that produced Finding 3. The cadence is too coarse to prevent recurrence.

**Mechanism D — Registration-as-commissioning.** A document is not binding until registered. Authoring is two commits: the document, then the Map update. Selected: couples registration to commissioning so binding-status and registration cannot drift — they are settled in the same authoring act. The two-commit pattern is natural under the project's existing one-topic-per-commit discipline.

### 6.2. The doctrine: registration-as-commissioning

A binding document's lifecycle has three states under M4:

- **Authored, unregistered: provisional.** The document exists on disk and in the commit history. It is operational and consultable. It is *not* authoritative — no session, no advisory turn, no AI-assisted reasoning episode treats it as binding doctrine. It may be cited as "currently provisional" pending registration.
- **Authored, registered: binding.** The Map has been updated to reflect the document at its determined tier. The Compression Rule (§3.1) operates against it: Tier 0–2 binding by default, Tier 3+ reference-only.
- **Authored, registered, retired or superseded: archived.** A future state the registration mechanism supports — registration is not permanent; documents can be re-classified or retired by subsequent Map updates. Outside scope of this memo.

The provisional state is not a workaround. It is the deliberate gate that prevents Finding 3 from recurring. Documents like the Operational Plan v1.1 and the Compact were authored, committed, and operated against as binding without ever being registered in the Map — the project skipped the registration step. Under M4, those documents would have been provisional from their initial commit until their Map registration shipped; sessions in between would have known to consult them as provisional, not authoritative.

### 6.3. The enforcement: pre-commit gate for `docs/`

A pre-commit gate detects additions of new top-level documents under `docs/` and fails the commit if the Documentation Map has not been modified in the same staging set. This is a supporting enforcement, not the primary mechanism — the doctrine in §6.2 is the primary.

The gate's scope is intentionally narrow: it catches `docs/` additions because `docs/` is the canonical home for binding doctrine. It does not catch `_observations/` additions because `_observations/` legitimately contains non-binding observation memos. The Tier 5 doctrine v1.0 case (`1cf4142`, filed in `_observations/` as provisional) is therefore not caught by the gate; the doctrine in §6.2 is what governs it — the doctrine ships unregistered, is provisional, and registers when promoted to `docs/` (which, for the Tier 5 doctrine, is gated on empirical validation per its own §1 framing).

The gate's implementation is a follow-on engineering task, named in the standing backlog (§10) as a v1.6-Map-coupled work item. Until the gate ships, the doctrine in §6.2 alone is the discipline; the gate hardens it but does not constitute it.

### 6.4. The bootstrap: v1.6 Map as the act that establishes the mechanism

M4's chicken-and-egg: registration-as-commissioning requires a Map to register against, but the current Map (v1.5) lacks the unregistered binding documents (Finding 3) and lacks the Compression Rule and Canonical Declaration that §3 reinstated. The v1.6 Map shipping in §7 is the bootstrap: it registers the ten unregistered documents at the tiers §5 classified, reinstates the Compression Rule and Canonical Declaration in the index itself, reflects the Business Plan's binding-vision-source carve-outs from §4, and establishes the registration-as-commissioning mechanism in its preamble such that the v1.6 Map is the first artifact registered under the mechanism it codifies.

This is reflexive but not circular. The Documentation Map is not itself a source of substantive doctrine — it is the authoritative registry of doctrine status, tier placement, and loading rules. The Map records *which* documents bind and at *what* tier; it does not itself constitute the binding doctrine the documents carry. Under M4 going forward, Map revisions are registry updates: a new Map version supersedes the prior one and registers any new binding documents authored since, with each Map version carrying its own version designation as the registration record. The v1.6 Map's bootstrap status is the special case; v1.7 and onward operate under the established mechanism without requiring this memo's curative authority.

### 6.5. What this resolution does and does not do

**What it does.** Establishes the procedural doctrine that prevents Finding 3 from recurring. Couples registration to commissioning. Names enforcement (the gate) and doctrine (registration-as-commissioning) as separable but complementary. Defines the provisional state explicitly so sessions consulting unregistered documents know how to treat them.

**What it does not do.** Does not require retroactive provisional-status for the ten currently-unregistered documents — they are classified as binding in §5, with the v1.6 Map's bootstrap shipping the registration. Does not author the pre-commit gate; that is a follow-on engineering task. Does not specify the v1.6 Map's content beyond the framework §3, §4, §5 establish; that authoring is commissioned in §7.

**Curative ratification (one-time amnesty).** The ten documents listed in §5 are granted binding status effective immediately upon this memo's commit. The v1.6 Map will formally register their binding status in the canonical index, but the binding authority begins with this memo's commit, not with v1.6's. This is a one-time curative act addressing the specific Finding-3 documents that pre-date the M4 mechanism. The amnesty applies only to the §5 reset set and may not be invoked for documents authored after this memo's commit. Documents authored after this memo's commit are subject to the M4 registration-as-commissioning doctrine in §6.2 without exception: they are provisional until registered, regardless of how substantively binding their content appears to be. The amnesty is the bridge between the pre-M4 era and the M4 era; it is not a recurring escape hatch.

### 6.6. Linkage to §7 (M5)

§6 establishes the registration mechanism. §7 commissions the v1.6 Map as the first artifact that operates under it (and, reflexively, registers itself).


---

## 7. M5 — Documentation Map v1.6 commissioning

**Resolution.** Documentation Map v1.6 is commissioned as a follow-on artifact to this memo. v1.6 is *not* authored in this session — that is a separate authoring session with its own session brief. v1.6's predecessor is this memo at its commit hash plus the v1.5 Map (`SquadVault_Documentation_Map_v1_5__1_.docx`) for content lineage.

### 7.1. v1.6 scope (what v1.6 must include)

The v1.6 Map's authoring session inherits the following commitments from this memo:

- **Reinstate the Compression Rule and Canonical Declaration in the Map itself,** verbatim per §3.1 and §3.2. The v1.5 silent-retirement of these rules is the failure mode v1.6 corrects; their explicit presence in v1.6 is non-negotiable.
- **Register the ten unregistered binding documents** at the tiers §5.1 specified. The summary table at §5.2 is the working list. The Compact's Tier 1 placement, the Tier 5 doctrine's provisional-Tier-1 framing, and the Internal Note's Tier 3 reference classification all transfer to v1.6 without revision unless a v1.6 authoring session surfaces evidence to the contrary.
- **Reflect the Business Plan's binding-vision-source tier** with the per-§ carve-outs from §4.2 and §4.3. v1.6 may name a new tier label for the Business Plan's vision sections (e.g., "Tier 0V — Vision Source") or may include them as a special-case annotation under existing tiers; the choice is the v1.6 authoring session's. The substantive binding-status (Founder's Letter, §3¶1–2, §5¶1–3, §6, §7 binding-vision; everything else reference) does not change.
- **Codify the registration-as-commissioning mechanism in the Map's preamble** per §6.2. v1.6 is the first artifact registered under this mechanism (the bootstrap framing per §6.4); v1.7 and onward operate under it normally.
- **Preserve v1.5's structural improvements** — registration of Selection Set Schema and Rivalry Chronicle as Tier 2; the Conceptual Components section flagging Social Layer as deferred — without revision.

### 7.2. What v1.6 does not do

v1.6 does not author new doctrine. It is the operational index that reflects doctrine authored elsewhere. v1.6 does not re-deliberate M1, M2, M3, or M4; those resolutions are inherited from this memo. v1.6 does not author the pre-commit gate from §6.3; that is a separate engineering follow-on.

### 7.3. v1.6 authoring session

The authoring session for v1.6 is named in the standing backlog (§10) as a follow-on with this memo as predecessor. Session shape: doc-only, single artifact, single wave; no production-path code changes; one commit (the v1.6 Map). Filing: `docs/SquadVault_Documentation_Map_v1_6.md` (or `.docx` if the v1.6 authoring session elects to match the v1.5 file format; per the format-decision precedent at `14c6003`, `.md` is preferred for new authoring).

The v1.6 Map's authoring is gated only on this memo's commit. Once this memo lands, v1.6 may be authored at any time. Its authoring is the gating condition for unblocking the gap audit (which inherits its binding-document scope from the v1.6 Map's registered list).


---

## 8. Phase 11 — Product Surface: framing and discipline

**Resolution.** Phase 11 (Product Surface) is the active phase for new development work, running in parallel with Phase 10's in-flight 2025 season operational concerns. Phase 11 ships under what this memo names **Apple-discipline**: constraint over breadth, surfaces shipped exquisitely rather than broadly, and a per-surface constitutional memo for every surface that ships. The Constitution's integrity principles bind every Phase 11 surface; the recalibration arc's retired scope restrictions do not.

### 8.1. Phase 11's scope, in framing terms

Phase 11 is the phase in which SquadVault begins to express its Business Plan vision through shipped product surfaces. Phase 10's substrate work — deterministic recap engine, governed expressive output, append-only canonical events, integrity-bound facts — produced the foundation. Phase 11 is the foundation made visible to a user.

What Phase 11 *is* in framing terms:

- The phase where SquadVault becomes more than a recap engine.
- The phase where the digital-clubhouse vision the Founder's Letter articulates begins to ship as user-facing surface.
- The phase where the Tone Engine's multi-tone capability, the Hall of Fame & Shame, the League Chat Replays, the Personal Vaults — the §6 Business Plan features that the substrate has been the foundation for — begin to ship one at a time, exquisitely.

What Phase 11 *is not* in framing terms:

- Not a feature roadmap. The Business Plan §6 is the feature horizon; Phase 11 ships against that horizon one surface at a time without committing to a sequence.
- Not a launch phase. SquadVault's first user-facing artifact is the recap that is already shipping; Phase 11's surfaces are additional expressions, not the launch of the product.
- Not the multi-modal multi-tenant social platform. That is Phases 12+; Phase 11 is the predecessor that demonstrates the Apple-discipline can ship surfaces without violating the integrity principles before the project takes on the larger integration challenge.

### 8.2. The Apple-discipline doctrine

The doctrine governing Phase 11 surface authoring:

**Constraint over breadth.** Phase 11 v1.0 ships one or two surfaces, not five. A broader minimum-viable launch is rejected — not because broader scope is impossible, but because the project's discipline is to demonstrate exquisite ship before scaling ship. The Business Plan's §6 feature list is a horizon, not a near-term target.

**Exquisite ship.** Each Phase 11 surface ships at production quality the first time it ships. Iteration toward quality after broad release is rejected. This is not perfectionism; it is the corollary of the integrity principles — facts immutable and append-only means quality cannot be retroactively patched in (the data is already in the ledger), and silence over speculation means features must ship at the quality threshold their first publication earns the user's trust at.

**Per-surface constitutional memo.** Every Phase 11 surface that ships gets its own constitutional memo, in the shape of the Tier 5 doctrine's `1cf4142` precedent: provisional-binding doctrine in `_observations/`, promoted to `docs/` upon empirical validation by one or two real cycles of the surface in operation. The constitutional memo names what the surface is *for*, what integrity principles bind its implementation, and what the surface forbids itself from adding (the reciprocal of "what we are not" at surface-scope).

**Integrity inheritance.** Every Phase 11 surface inherits the Constitution's integrity principles without exception. Facts immutable, narratives derived, AI assists humans approve, silence over speculation, no analytics, no optimization, no engagement loops, no prediction. The recalibration arc's retired scope restrictions (single-league, single-tone, text-only, no frontend, no multi-modal, no discussion surface) do not bind Phase 11 surfaces — that retirement is what makes Phase 11 possible — but the integrity principles do.

**No new foundations.** The substrate's architecture is complete (the Implementation Excellence Plan shipped at `b9f495c`). Phase 11 may add surfaces, adapters, and artifacts. Phase 11 may not add new foundational layers — new core abstractions, new integrity-tier rules, new architectural primitives — unless a shipped surface demonstrates a concrete failure that cannot be solved within the existing Core Engine, Writing Room, Creative Layer, Editorial Attunement Layer, or human-approval model. The default response to a hard product question is not a new layer; it is a clearer expression of the existing layers. This pillar prevents the AI-assisted failure mode in which every difficult surface question becomes an architectural-expansion proposal. The existence of a binding vision horizon does not authorize parallel surface expansion or foundational expansion; it authorizes one or two surfaces shipped exquisitely against the existing substrate.

### 8.3. The alternative framing, named for completeness

A "broad MVP" framing was available — ship Phase 11 surfaces minimally-viably across multiple horizon-features at once, iterate toward quality after release. This framing is not chosen. It was the implicit shape of venture-pitch §11 and §17 (the Business Plan's growth-mechanics sections, classified reference-only at §4.3); it is the shape that growth-mechanics framings would prefer because broad release accelerates engagement metrics. The recalibration arc's clarity about scope-restriction retirement does not extend to growth-mechanics adoption (§2.7); Apple-discipline's constraint-over-breadth is the doctrine that protects the integrity-tier inheritance from drifting toward growth-mechanics framings under iteration pressure.

### 8.4. The relationship to Phases 12+

Phase 11 demonstrates that Apple-discipline can ship surfaces without violating integrity principles. Phases 12+ scale the demonstration: multi-modal expansion (audio, video, image-rich recap surfaces), multi-tenancy (multiple leagues with isolation), social-surface elements (Hall of Fame & Shame at user-facing scale, League Chat Replays as archived shared surface), the multi-tone Tone Engine. Phase 11 is the predecessor that earns Phase 12+ the confidence the integrity-tier discipline scales.

Phase 12+ does not begin until a **Phase 11 Closure Memo** is authored that empirically certifies the Phase 11 outcome. The Closure Memo is a binding doctrine artifact (subject to the M4 registration-as-commissioning mechanism in §6.2) authored after at least one Phase 11 surface has shipped, been used by the founder's league for at least one full cycle, and been reviewed against the criteria below. The Closure Memo's required certifications:

- **Surfaces shipped.** Which Phase 11 surfaces shipped, with commit references and per-surface constitutional memos cited.
- **Integrity violations, if any.** Whether any shipped surface introduced analytics, optimization, engagement loops, prediction, or other integrity-tier violations. If yes, the Closure Memo names what happened, why it shipped, and what was done about it.
- **Qualitative league response.** Founder's-league response to the surfaces — not engagement metrics, but qualitative judgment of whether the surfaces felt like the league's memory or like a product trying to extract attention.
- **Apple-discipline assessment.** Whether the surfaces shipped exquisitely (production quality first time) or whether iteration pressure produced shipped-then-fixed patterns. If the latter, what the failure pattern reveals about the discipline.
- **Growth-mechanics drift, if any.** Whether any product, design, or operational decision during Phase 11 drifted toward growth-mechanics framings, even if not shipped. Drift in framing is a leading indicator of drift in implementation.
- **Trust failures, if any.** Any case where a shipped surface produced output the founder or league found incorrect, fabricated, manipulative, or otherwise trust-breaking.

The Closure Memo's role is to make Phase 12+ authorization an explicit binding act, not a default continuation. Phase 12+ work — multi-modal expansion, multi-tenancy, broader social-surface elements, the multi-tone Tone Engine at scale — is not authorized by this memo. It is authorized by the Closure Memo, if and when the Closure Memo certifies the Phase 11 outcome justifies it. The recalibration arc's vision affirmation commits the project to honoring the Phase 12+ destination as a possible horizon; it does not commit the project to that destination regardless of Phase 11 outcome. Phase 11 is therefore both a phase and a doctrine-validation exercise; the Closure Memo is the doctrine that records which validation occurred.

### 8.5. What §8 does and does not do

**What it does.** Names Phase 11 as the active phase for new development. Establishes Apple-discipline as the doctrine governing Phase 11 surface authoring. Names the per-surface constitutional-memo discipline. Names integrity inheritance and the corresponding doctrine that the retired scope restrictions are not re-imposed at surface scope. Names the relationship to Phases 12+ and the gating logic.

**What it does not do.** Does not specify Phase 11's actual surfaces — which surface to ship first, what features to express, what UI shape any surface takes. Surface specification is a separate authoring session per the per-surface constitutional-memo discipline. Does not commit to a Phase 11 timeline; the discipline is exquisite ship, not scheduled ship. Does not author any Phase 11 surface's constitutional memo; those are separate follow-on artifacts.

### 8.6. Linkage to §9 (disruption-vs-artisan)

§8 names Apple-discipline. §9 deliberates the broader artisan-vs-disruption question that Apple-discipline implicitly takes a stance on. §8's stance is: integrity-discipline over both pure-artisan and pure-disruption framings; empirical posture deferred to Phase 11's actual surface outcomes. §9 articulates this minimum-stance explicitly.


---

## 9. The disruption-vs-artisan question: artisan frame primary, disruption legitimate but conditional, integrity-discipline binds both

**Resolution.** The artisan frame is the project's primary success criterion: an elegant product, built on the foundation of truth the integrity principles establish, served exquisitely to the founder's longtime fantasy football league and to other leagues that find the product. The disruption frame — viable business opportunity at scale, the trajectory the Business Plan's growth-mechanics sections describe — is a legitimate and welcome aspiration but conditional on the artisan frame's success and on the integrity discipline scaling with the product. Phase 11's actual surface outcomes will produce the empirical evidence that lets a future memo engage the disruption frame more substantively. v1.0 names the prioritization and articulates the conditions under which the disruption frame becomes operational doctrine rather than aspirational horizon.

### 9.1. The two frames, briefly

Two frames have been available to the project since its inception. The disruption frame: SquadVault is a category-creation move, ships at scale, competes with Yahoo / ESPN / Sleeper for fantasy-league mindshare, succeeds by network effects and broad adoption, follows the venture-pitch trajectory the Business Plan's growth-mechanics sections (§11, §17, §19) describe. The artisan frame: SquadVault is a small product served exquisitely, succeeds by being uncompromising about integrity discipline rather than by being broadly adopted, follows the trajectory the substrate's actual development has taken — careful, deliberate, integrity-bound, allergic to optimization-as-success-criterion.

The two frames are not entirely incompatible. They imply different design decisions, different success criteria, and different relationships to the Business Plan's growth mechanics. They cannot both be primary; one must be downstream of the other.

### 9.2. The prioritized stance

The artisan frame is primary. Its success criterion: an elegant product the founder's longtime fantasy football league loves, built on the foundation of truth the integrity principles establish. This success criterion is achievable independent of any business outcome and is the project's binding goal. If the project ships under the artisan frame and never produces business viability, it has succeeded by its own primary measure.

The disruption frame is a legitimate aspiration, conditional on two things:

- The artisan frame succeeding first. Disruption-shape scaling that has not first cleared the artisan-shape threshold is not the trajectory this doctrine endorses.
- The integrity discipline scaling with the product. A multi-modal multi-tenant social-platform SquadVault that violates the integrity principles is not SquadVault under either frame; the disruption frame's legitimacy is conditional on the integrity discipline holding through scale, not on the disruption being achieved at any cost.

Under both conditions, disruption-shape outcomes are welcome. The Business Plan's vision of SquadVault as the emotional engine behind every fantasy football league is honored, not retired, by this prioritization. What the prioritization rejects is *disruption as primary success criterion* — the framing that would treat artisan-frame success as a stepping stone or a prelude to the "real" success of broad scale. The artisan-frame outcome is the real success; the disruption-frame outcome is the welcome co-outcome.

The integrity discipline binds both frames. A SquadVault that ships disruption-shaped and violates the integrity principles is not SquadVault. A SquadVault that ships artisan-shaped and violates the integrity principles is also not SquadVault. The distinguishing characteristic of the project is the integrity discipline, not the scale-shape; the prioritization between the frames operates within the integrity-tier discipline, never outside it.

### 9.3. The Apple lineage

The Apple-discipline framing in §8 is recognizably Apple lineage, and the lineage is not coincidental. The founder grew up Apple / Jobs in San Jose, and the artisan frame and the Apple frame are not separable in his hands. Naming this is the honest version of the doctrine. The alternative — pretending the framing arrived from generic design literature rather than from a specific personal-design-vocabulary — would be the more durable doctrine but the less truthful one.

The Apple lineage also resolves an apparent tension. Apple under early Jobs (1976–1985) was disruption — personal computing as category creation. Apple under returned-Jobs (1997–2011) was the artisan shape *applied at scale* — the iPhone shipped to a billion people, and the discipline was the reason it could. The frame the project inherits is neither pure-artisan nor pure-disruption; it is *the integrity discipline that lets the artisan frame scale without becoming the thing the discipline was meant to prevent*. SquadVault may legitimately scale to multi-tenant multi-modal social-platform shape (the Phase 12+ horizon) without violating the artisan-primary stance, *if* the integrity discipline scales with it. That conditional is the doctrinal mechanism by which the artisan-primary stance accommodates disruption-shaped outcomes; it is also the gate that prevents disruption-shaped outcomes from displacing the artisan-primary stance.

### 9.4. Empirical posture deferred

A successor memo — Reset Memo v1.1, or a separate Phase 11 surface-evaluation memo — engages the disruption frame more substantively after Phase 11's first surfaces ship. The empirical evidence that question requires is not yet available; deliberating it under v1.0 would be premature.

Specifically, what successor deliberation needs:

- The Phase 11 v1.0 surface (or two) actually shipped, with empirical evidence on whether Apple-discipline produced exquisite ship at the artisan-frame threshold.
- Real qualitative response from the founder's league and any additional leagues that find the product (not engagement metrics — the integrity principles forbid those as success criteria — but qualitative response, the kind that distinguishes "users love this" from "users tolerate this"). The artisan-frame primary success criterion is whether the founder's longtime league loves it; that signal is qualitative and primary.
- Empirical evidence on whether business viability surfaced as a legitimate co-outcome — whether the artisan-frame-disciplined product produced revenue, partnership, employment, or other business-shaped outcomes the founder values. This is not the primary success measure but is the empirical input the successor deliberation needs to engage the disruption frame substantively.

Until those three are available, the disruption frame is unanswerable in any way that doesn't reduce to founder hope or founder doubt. Founder hope and doubt both matter but are not by themselves binding doctrine. v1.0 names the prioritization and the conditions; v1.1+ produces the empirical resolution.

### 9.5. What §9 does and does not do

**What it does.** Names the disruption-vs-artisan question as real. Articulates the artisan-primary stance with disruption as legitimate-but-conditional aspiration. Names the two conditions under which disruption-shape outcomes are welcome (artisan-frame success first; integrity discipline scaling with the product). Names the Apple lineage explicitly, including its personal source. Names the empirical conditions under which successor memos can engage the disruption frame more substantively.

**What it does not do.** Does not retire the disruption frame; the Business Plan's vision of SquadVault as a multi-tenant multi-modal social platform is preserved as a legitimate Phases 12+ horizon. Does not commit Phase 12+ to either trajectory unconditionally; the §8.4 gating logic stands and is reinforced here. Does not articulate the founder's specific personal or economic context as binding doctrine; that context is real and is the ground reality the framing operates within, but it changes, and binding doctrine that names situational specifics tends to age awkwardly. The artisan-primary-with-disruption-aspirational posture is what this memo commits to; the situational specifics that produced that posture are background context not encoded here.


---

## 10. Standing backlog after this memo

The reset memo's commit retires the M1–M5 standing-backlog item from the gap-audit closure memo's §7. It commissions four new items, unblocks one, and leaves the carry-forward Tier-5-monitored items unchanged.

### 10.1. Retired

**M1–M5 deliberation.** The reset memo *is* the M1–M5 resolution. Closure memo `2dda2c2` §7 named "Reset Memo v1.0" as the active backlog item; this memo's commit retires it.

### 10.2. New, active

**v1.6 Documentation Map authoring.** Predecessor: this memo. Per §7.1, v1.6 reinstates the Compression Rule and Canonical Declaration, registers the ten unregistered binding documents at the tiers §5.1 specified, reflects the Business Plan's binding-vision-source carve-outs from §4.2/§4.3, and codifies the registration-as-commissioning mechanism in its preamble. Filing default `docs/SquadVault_Documentation_Map_v1_6.md`. Doc-only, single artifact, single wave. Gating: only this memo's commit. The v1.6 Map's authoring is the gating condition for unblocking the gap audit (per §10.3 below).

**Pre-commit gate for `docs/`-without-Map enforcement.** Predecessor: this memo. Per §6.3, a pre-commit gate detects additions of new top-level documents under `docs/` and fails the commit if the Documentation Map has not been modified in the same staging set. Engineering task, not doc work; lives in `scripts/` or `.git/hooks/`. Implementation can ship after v1.6 lands or in coordination with v1.6. Until the gate ships, the doctrine in §6.2 alone is the discipline.

**Phase 11 surface specification (first surface).** Predecessor: this memo, specifically §8. Phase 11's first surface authoring session ships its own constitutional memo per the §8.2 per-surface discipline, in the shape of `1cf4142` (provisional doctrine in `_observations/`, promotion to `docs/` upon empirical validation). The reset memo does not specify which surface ships first; that is the Phase 11 surface-specification session's call. Apple-discipline (§8.2) constrains the work; integrity inheritance (§8.2) binds it. The first surface is not gated on v1.6 Map authoring — Phase 11 work can begin in parallel.

**Per-surface Phase 11 constitutional memos (framework, no specific surface).** Standing framework rather than discrete backlog item. Every Phase 11 surface that ships gets one. Predecessor for any specific surface memo: the Phase 11 surface-specification session that authored it.

### 10.3. Unblocked

**Gap Audit Document Reconciliation v1.0.** Was BLOCKED on M1 per closure memo §7 item 2. M1 is now resolved (§3 of this memo); the gap audit can proceed against the binding-document scope this memo establishes. Practical gating: the gap audit's per-document review benefits from operating against the v1.6 Map's registered list rather than this memo's §5 classification table, so the audit may elect to defer its run until v1.6 ships. That is the gap-audit session's call; the memo does not require deferral.

### 10.4. Carry-forward (Tier-5-monitored, unchanged)

The following items carry forward from the closure memo's §7 unchanged. None are blocked by this memo; none are retired by this memo. Tier 5 doctrine v1.0 governs their re-activation cadence per `1cf4142`.

- Cat 3c row-76 (W14 2025 paragraph-end record-claim attribution edge case)
- Snap-outcome detection (B3 latent path, separate from row-25 thread)
- Player-streak verb inversion diagnostic (T9 STALE_CLAIM thread)
- NOTABLE-pass alphabetical lockout (volume-vs-cap diagnosis, governance call deferred)
- Bug 1 classifier current-week scope (extension to multi-week scope)
- Tier 5 doctrine v1.1 trigger (one or two real W14+ 2026 cycles produce empirical evidence; v1.0 promotes to `docs/` or revises to v1.1)
- Framing B wrapper (deferred from earlier session)
- Priority-list mechanism redesign (5th-instance meta from closure memo §6)

### 10.5. Sequencing

The reset memo does not prescribe the order of new-active items. Recommended sequencing for the immediate next session:

1. **v1.6 Map authoring** is the natural successor — it bootstraps the registration mechanism (§6.4) and unlocks the gap audit's preferred run-condition. Single-session work, light deliberation, predominantly mechanical.
2. **Phase 11 first-surface specification** can begin in parallel; not blocked on v1.6.
3. **Pre-commit gate engineering** can ship at any time after v1.6 lands; coordinate with v1.6 commit if practical.
4. **Gap audit** runs after v1.6 if the audit elects the v1.6-as-substrate framing; can run earlier against this memo's §5 classification if the audit elects the more-immediate framing.

The recommended sequencing is not binding; the founder elects ordering per session-by-session judgment.


---

## 11. Methodology notes

The reset memo's authoring revealed several patterns worth surfacing for future contributors. None are doctrine; they are observations about how the project's working process operated under the load this memo's deliberations imposed.

### 11.1. Reset-memo-as-formalization-of-arc

The recalibration arc that ran during the 2026-05-07 session settled substantive doctrine — integrity-vs-scope distinction, Business Plan as binding-vision-source, niche-agnosticism architecturally backed, Phase 11 active — but settled it in conversation context rather than in a binding artifact. The reset memo is the artifact that formalizes the arc. Without it, future sessions would have operated from conversational memory of shifts that never made it into a binding document, and a strict-construction reading of the existing canon would have reached conclusions the arc explicitly retired.

The pattern is reusable. When a substantive recalibration occurs in conversation, the disciplined response is to author the formalizing artifact within a small number of sessions of the recalibration itself. The reset memo took two sessions (closure memo `2dda2c2` plus this memo) and approximately one calendar week from the recalibration to commit. Longer gaps risk the recalibration drifting back into ambiguity; shorter gaps risk the formalization landing before the recalibration has been empirically tested in any subsequent session.

### 11.2. M1–M5 sequencing as actually experienced

The closure memo named M1–M5 as ordered (M1 gating, M2 building on M1, etc.). The actual authoring confirmed the sequencing but also revealed the cognitive-weight distribution:

- **M1 was gating but tractable.** Three readings, Reading C strongest by clear margin once the frames were laid out. ~30 minutes deliberation, ~30 minutes draft.
- **M2 was the heaviest.** Three frames, the actual document (the Business Plan) needed to be present and re-read for per-§ carve-outs to be drawable. The authoring required re-uploading the document mid-session and reading several sections cover-to-cover. ~75 minutes total, the longest single section in the memo.
- **M3 was mechanical-once-framework-set.** §3 and §4 established the framework; §5's per-document classification flowed from it. ~30 minutes total, predominantly enumeration.
- **M4 was procedural.** Four mechanisms considered, Mechanism D selected with B as supporting enforcement. The hybrid required articulating the bootstrap (§6.4) which was the trickiest authoring move in the section. ~25 minutes.
- **M5 was thin commissioning.** Three subsections, no deliberation; the memo's job was to commission v1.6, not author it. ~15 minutes.

A pattern worth naming: when the closure memo named M-questions in numerical order, the order tracked dependency rather than cognitive weight. M2's heaviness was not predictable from its position in the list. Future memos commissioning multi-question sessions may benefit from naming both the dependency order and a cognitive-weight estimate, so that session-time pacing can be planned accordingly.

### 11.3. Multi-frame deliberation discipline as practiced

The brief's anti-drift §8 named multi-frame deliberation as a working-process commitment. The discipline operated explicitly at four substantive picks:

- M1 picked Reading C among three readings.
- M2 picked Reading B among three frames.
- M4 picked Mechanism D among four mechanisms (with B as supporting enforcement).
- §9's prioritized-stance shifted from even-handed to artisan-primary after Steve's personal disclosure surfaced binding context the original draft hadn't accounted for.

In each case the discipline produced visible deliberation rather than collapsed-to-preferred-frame resolution. Where Claude named a preference at the end of frame articulation, the preference was named explicitly so the deliberation remained transparent and the founder's decision was made on the merits rather than on momentum. Where Claude's preference was followed (M1, M2, M4), the deliberation produced a record of *why* that frame was selected, which is the record successor memos will rely on. Where Claude's preference was overridden (the §9 pivot), the deliberation produced a record of why the override was warranted.

The discipline costs time and produces longer artifacts. The cost is the price of the legibility — both for future contributors and for future-self.

### 11.4. Confidence labeling as practiced

Confidence labels — "high-confidence," "medium-confidence," "lower-confidence" — appeared at most substantive Claude turns during authoring. The labeling mattered most specifically at:

- **M2 frame articulation.** Claude flagged that confirmation-bias from the recalibration arc's pre-naming meant Claude's preference for Reading B should be discounted. The §4.5 caveat in the memo formalizes this.
- **§9 prioritized-stance pivot.** Steve disclosed personal context (unemployment, age, market) that revised what the prioritization should be. Claude offered three options (keep as drafted / revise the stance / add personal context explicitly) with explicit confidence labels on each, and Steve picked medium-confidence Option 2.
- **§10.5 sequencing.** Claude named the recommendation as "recommended sequencing," explicitly not binding, and flagged that founder judgment elects ordering per session.

The labeling discipline doesn't produce different deliberation; it produces deliberation that future contributors can audit. A claim labeled "high-confidence" comes with implicit accountability — if the claim turns out wrong, the labeling locates the error in the claim itself rather than in the absence of articulated confidence.

### 11.5. Substance-pushback discipline, two instances

The collaboration asymmetry — *Claude reserves right to slow Steve down on substance* — operated in two instances during this session, with different outcomes:

**Instance one: pre-§4 over-read.** Claude read fatigue signals into Steve's "I honestly don't know" response on §4 source-material handling, escalated to a recommendation to halt the session. Steve corrected: he was sharp in the moment but Claude's question was unclear. The escalation was Claude error — diagnosing cognitive state when the actual problem was Claude clarity. The pattern of conflating "Steve is fatigued" with "Claude was unclear" is worth flagging; it patronizes the collaborator and substitutes diagnosis for clarification. The corrective is to ask the clarifying question first and only escalate after evidence accumulates.

**Instance two: §9 prioritized-stance pivot.** After Steve's personal disclosure about unemployment and the artisan-vs-business priority, Claude correctly slowed down the §9 authoring to revise the stance from even-handed to artisan-primary. The substance pushback produced a better artifact than the originally-drafted §9 would have been. This is the discipline operating as intended: not diagnosing the collaborator's state, but pushing back on whether the doctrine matches the actual position the collaborator holds.

The distinction worth preserving: substance-pushback operates on the *artifact*, not on the collaborator. Claude pushes back on whether the doctrine matches the founder's actual position. Claude does not push back on whether the founder's faculties are intact. The first is in scope; the second is not.

### 11.6. Bottom-up TL;DR discipline

The memo authored §1 (TL;DR) last, after §2 through §11 were complete. The discipline was named explicitly in the brief: TL;DRs authored before deliberation tend to anchor deliberation in ways that resist updating; TL;DRs authored after deliberation can synthesize what actually landed.

The discipline served the memo. Specifically: §9's prioritized-stance pivot would have required revising a pre-authored TL;DR to match. Authoring §1 last means the TL;DR reflects what the memo actually settled, not what the memo was expected to settle.

A successor memo authoring multi-question doctrine may consider the same discipline. The cost is that the memo lacks a stable thesis statement during authoring; the benefit is that the eventual thesis matches the deliberations rather than constraining them.


---

## 12. Files and commits referenced

### 12.1. Commits

- **`b9f495c`** — Implementation Excellence Plan complete (substrate readiness for the recalibration arc; cited in §2.2).
- **`14c6003`** — Weekly Recap Context Temporal Scoping Addendum promoted from `_observations/` to `docs/addenda/` (precedent for `_observations/`-to-`docs/` promotion; cited in §5.1 #8 and §7.3).
- **`1cf4142`** — Tier 5 Live Observation Cadence Doctrine v1.0 (precedent for provisional doctrine in `_observations/` with promotion gating; cited throughout, particularly §5.1 #10, §6.3, §8.2).
- **`9a4fa89`** — Gap Audit Document Reconciliation v1.0 session brief (predecessor authoring artifact; cited in §10.3).
- **`2dda2c2`** — Gap Audit halted at Finding 0 closure memo (immediate predecessor; the memo whose §6 named M1–M5 and whose §7 enumerated the standing backlog this memo retires/transforms; cited throughout).
- **`6f55e00`** — Reset Memo v1.0 session brief (immediate predecessor; the brief that scoped this memo; cited in the memo's header).
- **(this memo's commit hash, TBD)** — Reset Memo v1.0 (this artifact). The eventual hash is the predecessor for v1.6 Map authoring (§10.2), the gap audit unblock (§10.3), and Phase 11 first-surface specification (§10.2).

### 12.2. Documentation Map versions

- **v1.4** — `SquadVault_Documentation_Map_and_Canonical_References_v1_4_1.pdf` (project knowledge). The version that contained the Compression Rule and Canonical Declaration this memo's §3 reinstates verbatim. Cited as the doctrine-source in §3.1 and §3.2.
- **v1.5** — `SquadVault_Documentation_Map_v1_5__1_.docx` (project knowledge). The version that silently deleted the Compression Rule and Canonical Declaration; named as mistake in §3.4. Cited as the source v1.6 supersedes.
- **v1.6** — Commissioned in §7 of this memo as a follow-on artifact. Filing default `docs/SquadVault_Documentation_Map_v1_6.md` per §7.3.

### 12.3. Business Plan and appendices

- **`SquadVault_Business_Plan.docx`** (uploaded during the authoring session). Per §4.2: Founder's Letter binding-vision; §3 paragraphs 1–2 binding; §5 paragraphs 1–3 binding; §6 binding; §7 binding. Per §4.3: §4, §8, §9, §10, §11, §12, §13, §14, §15, §16, §17, §18, §19, §20–§24 reference-only.
- **Appendices A1–A26** (uploaded during the authoring session). All reference-only per §4.3.

### 12.4. Binding documents the memo references (per §5)

The §5 summary table (§5.2) lists the ten unregistered binding documents this memo classifies. The Constitution (Tier 0, registered in v1.5) is the apex authority cited throughout. Subordinate Contract Cards (Selection Set Schema, Rivalry Chronicle, FAAB Outcome Insight, Creative Layer, Editorial Attunement Layer) are cited in §3.5 as inheriting the Canonical Declaration's precedence.

### 12.5. The recalibration arc's conversation source

The recalibration arc that ran during the 2026-05-07 session is captured in conversation context only and is not a separately-committed artifact. This memo (specifically §2) is the formalization. The conversation source is preserved in the project's chat history; it is the substrate from which §2's formalization was extracted, not a binding artifact in its own right.

