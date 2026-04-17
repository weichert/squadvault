# Audit Follow-Up: Current Thinking on Open Design Questions — 2026-04-16

**Companion to:** `_observations/ARCHITECTURAL_AUDIT_2026_04_16.md`
**Status:** Current thinking, not commitments. Revisable as conditions change.
**Purpose:** For each open question the audit raised, record where I currently lean, what the reasoning is, what dependencies are unresolved, and what would change my mind.

---

## Preface

The architectural audit produced 12 open design questions (Section 10) and several entanglement hotspots (Section 8) that imply decisions. Publishing the audit without at least a preliminary response to those questions would make the audit feel like a problem statement without authorial judgment. This document is the authorial judgment.

A note on stance. I am not trying to answer every question definitively — several genuinely should not be answered yet, because the answers depend on facts that are not in hand (most obviously: the shape of a hypothetical second module). For those, the useful artifact is a clear statement of *what would need to be true* before a decision becomes tractable, not a coin flip dressed as a decision.

Where I do have a lean, I state it and show the reasoning. Where I don't, I name the missing input.

The questions are re-ordered here by clustering related ones, not by the original audit's ordering.

---

## Cluster 1 — The platform question

### Q1 (audit): Is "platform" the right aspiration, or is "well-factored monolith" enough?

**Current lean:** Well-factored monolith, for now. The platform framing is in the contract cards because the project's long-term vision imagines a second module; the code is a monolith because no second module exists and premature abstraction has a worse track record than late abstraction.

**Reasoning:** The audit's Section 5 finding — that the adapter contract is real-as-document, aspirational-as-code — reads to me as an honest accounting, not a problem. The contract describes a target state. The code currently implements one instance. The gap between them is what has not yet been built, and building it speculatively is the failure mode the project's constitution is explicitly designed to avoid. The memory-ledger seam at the bottom of the stack is already genuinely platform-clean (Schema §2 findings); that's the single place where premature investment would have been wrong to defer, and it wasn't.

What would change this: a concrete, non-hypothetical second module (specific contest shape, specific data source, specific audience). Until then, platformization work is investment against a speculative future, and the opportunity cost is work that serves the actual current module.

**Dependency on other decisions:** Q2 below.

### Q2 (audit): What is the smallest viable second module?

**Current lean:** I don't have an answer and I think trying to answer it now would be a mistake. The question itself is the right one, but it's a product question (what contest, what audience, what cadence) dressed in an architecture question's clothing.

**Reasoning:** The audit correctly points out that answering this question unlocks most of the others. What I can say is that not every fantasy sport is equally useful as the second module for architectural purposes. A fantasy basketball module would validate almost nothing about SquadVault's extensibility because it's structurally nearly identical to fantasy football — weekly head-to-head, players with positions, lineups, waivers. A fantasy golf module would validate the full schema's weekly-cadence assumption against a cumulative-scoring reality, which is where the real architectural stress lives.

The useful follow-up work here is product discovery, not engineering: is there a PFL-Buddies-analogous league for some other contest shape where the commissioner would find this useful? That's the research that should happen before module work begins.

---

## Cluster 2 — The adapter layer

### Q3 (audit): Where does the adapter interface live, if it becomes real?

**Current lean:** When Q2 has an answer and the second adapter is being built, the interface lives in `core/adapters/` as a `typing.Protocol`, and the MFL adapter is refactored to conform. Before that, it should not be extracted.

**Reasoning:** The contract card says "behavior contract, not ABC," which rules out the explicit ABC path but does not rule out `typing.Protocol` — Protocols are structural, runtime-implicit, and conform well to the project's stated preference for "boring, explicit code over clever patterns." `core/adapters/` is the right path because the protocol belongs with the core code that depends on it, not with any particular adapter's implementation.

The refactor is not trivial but is not exotic either. `MflClient` and `ingest_mfl_season` become conforming implementations. `DiscoveryReport`'s MFL-specific fields (`server`, `mfl_league_id`) either move to a `platform_metadata: dict` escape hatch or get separated into a per-adapter extended report.

What would change this: if the second module turns out to use a data source so different that "adapter" isn't even the right word (e.g., a manually-curated league with no external API), the question reframes entirely and the protocol might never be needed.

**Dependency:** Q1, Q2.

---

## Cluster 3 — The cadence and shape assumptions

### Q5 (audit): Does `week_index` become `period_index`?

**Current lean:** Not yet, and maybe never. If a non-weekly module is built, I'd prefer parallel per-module tables (`tournament_runs`, `daily_runs`) over a generalized `period_index` schema migration.

**Reasoning:** The audit is correct that `week_index` hardcodes weekly cadence into three primary keys. A generalized `period_index` looks cleaner in the abstract but carries two real costs. First, it's a schema migration of load-bearing tables (`recap_runs`, `recap_selections`, `prompt_audit`) that currently work correctly and have months of production data. Second, the "period" abstraction is genuinely leaky — a weekly period, a PGA tournament, and an NBA daily slate are not the same kind of thing, and forcing them into one column name trades clear semantics for false generality.

Parallel tables per cadence shape feel less elegant but are more honest. The detectors, verifier, and lifecycle would branch on cadence at the top level rather than at every query site. That's a larger code surface to maintain, but it's legible code — a reader can tell at a glance which module's pipeline they're in — where a unified `period_index` schema would require reading documentation to understand what "period 7 of season 2025" means for any given league.

What would change this: if the majority of a potential second module's code would be genuinely shared with the fantasy football module (same cadence family, same shape), then a generalization makes sense. For non-weekly modules, separation is cleaner.

### Q4 (audit): Does "module" mean fantasy-sport or fantasy-contest-shape?

**Current lean:** Contest shape. The meaningful architectural grouping is the shape (head-to-head weekly / cumulative seasonal / tournament), not the underlying sport.

**Reasoning:** Fantasy basketball and fantasy football share ~80% of a recap engine's architecture by virtue of having the same contest shape. Fantasy golf and fantasy football share almost nothing structural. Naming the module boundary by sport encourages per-sport duplication of the head-to-head machinery; naming it by shape encourages the shape's machinery to be the reuse unit.

This lean is consistent with how the audit classified detectors — `GEN` detectors are those that work for any head-to-head shape, not those that work for any sport.

**Dependency:** Q3 (protocol design depends on whether the boundary is sport or shape).

---

## Cluster 4 — Content registry and detector organization

### Q6 (audit): Do detectors self-register, or does a registry map categories to detectors?

**Current lean:** Self-registration via decorator, but not right now. Do it when a second detector family is added (platform-general vs football-specific split), not before.

**Reasoning:** The audit identifies the hand-maintained `CATEGORY_TO_DETECTOR` map as a maintenance hazard and the drift test's partial scope as a failure mode. Both are real. Self-registration solves both — a decorator like `@detector(id="D1", category="PLAYER_HOT_STREAK", dimension=1)` applied to each detector function collapses the map into a derived structure and makes the drift test trivially complete.

But the refactor touches ~60 functions' signatures and introduces import-time side effects (decorators populate a module-level registry at import). That's a lot of diff for a single-module codebase where the manual map is tractable. The payoff multiplies when there's a second detector family to register alongside — at that point, self-registration is clearly right.

In the meantime, the drift-test scope gap (Surprise S2 in the audit) should be closed. That's the integrity fix that doesn't require the full refactor.

**Dependency:** Q2 (if there's a second module, this becomes much more valuable).

### Q10 (audit): Where do the ~12 unmapped live categories go?

**Current lean:** They get D-numbered (or similarly-numbered) and added to the registry. The audit named them "primordial matchup detectors" (8), "bye week detectors" (3), and "scoring structure context" (1). None of these are orphans — they are load-bearing detectors emitting live categories. They should be accounted for.

**Reasoning:** The rationale for keeping them out of the map was likely historical: the three D-numbered files were the Narrative Angles v2 work, and the older `narrative_angles_v1.py` plus the bye-week/rules-context files predated that effort. That's a reasonable origin but a worse current state. All detectors that can emit a category into production should be in the registry.

Specifically I'd propose: primordial matchup detectors get a `P`-prefix (P1 UPSET, P2 STREAK, …P8 STANDINGS_SHIFT); bye week detectors get `B`-prefix (B1–B3); scoring structure gets `R1`. Or — if the `D`-prefix is meant to be dimension-agnostic — they get D51–D62 and the dimension scheme is extended. The prefix choice is a style call I haven't settled on.

This is the single concrete content-layer fix I'd put highest on the action list. It's the direct actionable from the audit's Surprise S2, and it both closes the integrity gap and makes the full detector inventory legible in one place.

### Q11 (audit): Does `core/exports/` stay in `core/` or move to a module path?

**Current lean:** Move, but low priority. The files are fantasy-football-module-specific and their current path contradicts the `core/` = platform-scope convention.

**Reasoning:** The audit's Hotspot #5 framing is correct. The cost is purely in import-path updates across the codebase and tests. I'd only do this as part of a broader module-boundary pass that also splits off `recaps/` content appropriately. Doing it in isolation creates import churn without making the module boundary meaningfully clearer, because nothing else is moving alongside it.

What would change this: if a second module is built and needs its own exports, at that point the whole `core/exports/` directory clearly needs to move out.

---

## Cluster 5 — The Writing Room question

### Q9 (audit): What happens to the Writing Room on the main path?

**Current lean:** Document the divergence explicitly, do not rewire the lifecycle through Writing Room intake unless a specific problem requires it.

**Reasoning:** This is the finding that bothers me the most in the audit (Surprise S3), because it is a canonical Tier-2 contract that the production lifecycle doesn't use. It's also the finding where rewiring would be most disruptive — the lifecycle's current path (recap_runs → canonical events → detectors → creative layer → verifier → artifact) works and is well-tested. Routing through Writing Room intake means inserting a signal-selection stage that the current code doesn't need, because detectors already do selection by virtue of their gating logic.

The honest assessment is that the Writing Room was likely scoped as a general signal-selection abstraction at a time when the detector layer was less sophisticated, and the detector layer has since grown to cover the same territory. The two coexist with overlapping responsibility; the detector layer won the orchestration battle by being directly callable.

Three options, in order of my preference:

1. **Document the divergence.** Add a section to the Canonical Operating Constitution or the Documentation Map acknowledging that the Writing Room is canonical-as-infrastructure for use cases that benefit from explicit signal selection (scripts, one-off analyses) but that the production weekly lifecycle deliberately uses detector gating instead. Acknowledge the conceptual overlap and treat it as resolved.
2. **Downgrade the Writing Room's canonical status** in the Documentation Map. This is more honest about current state but throws away work that might still be useful for non-lifecycle callers.
3. **Rewire the lifecycle through Writing Room intake.** This aligns code with contract but at meaningful risk to a production-tested pipeline. I would do this only if a specific failure of the current detector-gating approach required it.

I lean toward option 1 because it's the lowest-cost way to close the integrity gap between contract and code, and it preserves optionality.

This is also the most honest thing I can say in this document: a Writing Room rewire is the only bit of genuine architectural work the audit surfaced that *could* be done now, and I'm recommending against doing it. That's a judgment call and I want the judgment explicit.

---

## Cluster 6 — The voice and system prompt question

### Q7 (audit): Where does the system prompt for the creative layer live?

**Current lean:** Eventually it moves out of `creative_layer_v1.py` into module-owned resource files, but not via the schema (`league_voice_profiles` path the audit hypothesized).

**Reasoning:** The 200+ line football-specific system prompt embedded in `creative_layer_v1.py` is exactly the kind of module-content-in-platform-code that the audit flagged in Hotspot #8. The cleanest move is: the creative layer accepts a system prompt as a parameter; each module provides its own via a resource file (`src/squadvault/modules/fantasy_football/prompts/creative_system_prompt_v1.txt` or similar).

The audit hypothesized a database-resident version via `league_voice_profiles`. I disagree with that specific path because it conflates two different things: the system-prompt is module-design-time voice (how the chronicler speaks at all), while `league_voice_profiles` is league-configuration-time voice (how this specific league's chronicler adapts). Both exist. They should be separate layers. The system prompt belongs in code; the league voice profile adds to it at runtime.

This is low-priority because the current arrangement works and moving the string costs more than the current arrangement costs. But it's a natural step once a module boundary is being drawn for other reasons.

---

## Cluster 7 — Verifier organization

### Q8 (audit): Is the verifier one-per-module or one-per-platform-with-pluggable-checks?

**Current lean:** One-per-platform with pluggable checks, but the current monolithic 2843-LOC file doesn't make extraction obvious. I'd defer the split until a second verifier is being built.

**Reasoning:** The audit's analysis is correct — the claim-extraction infrastructure (regex, windowing, name matching, apostrophe normalization) generalizes; the category-specific check functions don't. The right target shape is a `verification_core/` with the infrastructure and per-module check registration.

But I don't think that's obvious from reading the current file. The file grew organically as categories were added, and the infrastructure is interwoven with the checks rather than cleanly separated. Extracting the infrastructure requires a refactor pass that understands which utilities are generic and which are category-specific — and that's a job best done when a second verifier is being built, because the second verifier's shape clarifies which utilities need to be exported.

What would change this: if the verifier accrues another 2–3 categories, it passes a complexity threshold where the monolith becomes hard to reason about, and the split becomes valuable on its own merits.

---

## Cluster 8 — Operational

### Q12 (audit): Are diagnostic scripts per-module or shared?

**Current lean:** Per-module once a second module exists, flat until then.

**Reasoning:** This is the lowest-stakes question in the list. `scripts/diagnose_purple_haze_series.py` is obviously PFL-specific; generic utilities like `scripts/diagnose_draft.py` are not. Splitting the directory is a one-weekend job when a second module justifies it. Doing it before that just adds paths.

---

## A question the audit did not raise

### QN (new): What is the design shape for resolving the tension between "silence over speculation" and "delight the audience"?

**Context:** The audit is oriented around architecture and governance integrity. It does not address a product-level tension that sits above both: the project's constitution strongly prefers silence over speculation, which is exactly correct for trustworthiness, and yet silence does not delight anyone. The product's success — insofar as "delight and intrigue end users" is a stated goal — depends on finding expressive ground inside the governance envelope.

**Current lean:** The resolution is in the data layer, not the constitution and not the creative layer. The established pattern ("give the model verified data and it cites verified data; withhold data and it invents") is the answer, applied at scale — every increment of delight comes from giving the creative layer more *kinds* of verified signal to draw on, not from relaxing governance on the signals it already has.

**Reasoning:** The audit's Section 9 Surprise S11 noted that SCORING_STRUCTURE_CONTEXT is load-bearing for model contextualization. That's a specific instance of the general rule: detectors that produce specific, concrete, verifiable observations expand the creative layer's expressive range without any change to governance. The player trend detectors in Dimensions 1–2 (11 detectors the project has scoped but not built) are the immediate next increment of this.

What the constitution's silence-preference rightly forbids is model-invented interpretation dressed as fact. What it does not forbid — and what the detector layer is specifically designed to enable — is the model drawing from a richer inventory of verified, concrete, specific observations. The tension is resolved by investing in detection, not by loosening verification.

**Why I'm including this question here:** because it is the product-level design question the audit's engineering framing didn't surface, and an audit-follow-up document that ignored it would be incomplete. A reader — or reviewer — who reads the audit and this document together should see that I understand the codebase's architectural state *and* the product tension that architecture is in service of.

---

## What this document is not

- A roadmap. The decisions here have varying urgency and varying dependencies; sequencing them is a separate conversation.
- A commitment. Every current lean in this document is revisable.
- An exhaustive treatment. Several of the audit's Section 8 entanglement hotspots have natural resolutions that I didn't write up here because they follow mechanically from the cluster-level answers above.

## What this document is

An honest snapshot of how I'm thinking about the audit's open questions as of the date of writing, with reasoning visible enough that a future reader (including future-me) can evaluate which leans held up and which should have been revised earlier.

---

*End of document.*
