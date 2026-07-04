# Session Brief — Unit 1.7b: Presentation Implementation + Lint

Date authored: 2026-07-04 (DECIDE session). Execution window: August 2026, after Draft Weekend prep allows, before NFL Week 1 (~09-08).
Session type: EXECUTE (fresh session), three founder gates (⛔ G1: structure design; ⛔ G2: tests; ⛔ G3: diff + merge)
Repo: engine — identity test must PASS
Plan reference: docs/Narrative_Presentation_Spec_v1_0.md (landed ce38f23) is the governing contract — read it in full before anything; Completion Plan Unit 1.7b; ratified D-F (standalone SOFT-tier lint, verifier stays purely factual)
Scope in one line: make the code obey the spec — canonical artifact structure pre-rendered at the derived layer, the plain-text/group-text renderer, and the deterministic presentation lint; this is what closes R5 at the implementation layer.

## Kickoff

You are an EXECUTE session for SquadVault Unit 1.7b. Read _observations/session_brief_unit_1_7b_presentation_implementation.md in full, then docs/Narrative_Presentation_Spec_v1_0.md in full — the spec governs; this brief only sequences it. CLAUDE.md ritual; three ⛔ gates, adjudicated by the founder with the DECIDE-lane continuity memo in hand. Hard rules: the spec's §6 prohibitions are law (renderers never add, remove, reorder, or rephrase content; never re-derive from data; facts block byte-identical, always last); the lint is SOFT-tier and standalone per D-F — it flags for human review, never blocks on ambiguity, never fabricates, and the verifier's factual contract is not touched; approved artifact text is rendered verbatim; empty sections omitted, never placeholdered; prod DB read-only, hashed start and end; nothing published; tests founder-ratified before implementation.

## 1. Objective

Implement the landed spec via the proven four-step playbook: (a) a canonical-structure module in render/ that parses an approved artifact into the spec §3 structure (masthead, title, lede, per-matchup, transactions, standings, facts block) exactly once at the derived layer — a malformed artifact is surfaced, never repaired; (b) the plain-text/group-text renderer per spec §4.1 (zero markup, whitespace-and-case structure, the single hyphen divider, no manual wrapping, no emoji), a pure function of the structure; (c) consumer refactor so distribution paths read the rendered form, with the facts block byte-identical through every path (E1.5b remains the gate); (d) the presentation lint per spec §7 — masthead present, title present, facts block intact and byte-identical, no channel-forbidden markup, paragraph bounds, no orphaned headers — SOFT-tier, standalone, reported alongside verifier results pre-approval. Web rendering per §4.2 is structure emission only from the engine (the frontend consuming W.2 roles is a later frontend unit); print per §4.3 is constraints-compliance in the structure, no renderer.

## 2. Successor adjudication notes

These gates will likely be held by an adjudicator other than the brief's author. What each gate is for: G1 exists to catch structure-model mistakes before code — the one question that matters is whether the parsing model can represent every existing approved artifact without loss (require the session to prove it against real artifacts, read-only). G2 exists to freeze test outcomes before implementation — check that every spec §6 prohibition has a test, that the lint has both a firing case and a non-firing case per check, and that byte-identity has a regeneration guard (TB.1-style: every existing artifact renders byte-identically through the refactored path). G3 is the joint review — the diff to read hardest is the consumer refactor (step c), because it touches paths that already work; the structure module and renderer are new code with frozen tests and read themselves. When in doubt at any gate, the standing rule is halt-don't-guess; a stopped session costs an hour, a guessed gate costs the record.

## 3. Constraints

- The spec governs. Where this brief and the spec diverge, the spec wins and the divergence is escalated (git-wins discipline, applied to contracts).
- Four-step order is mandatory: structure at data layer → renderer → consumer refactor → lint. No lint before the structure it lints exists.
- Zero behavioral change to approval, verification, or facts-block generation — this unit clothes approved artifacts; everything upstream is untouched, proven by regeneration byte-identity.
- Real-artifact fidelity: G1's structure model and G2's tests are validated against actual approved artifacts in the prod DB (read-only), not synthetic fixtures alone.
- Marker and provenance survival: any ATTESTED/external_source markers present in the facts block (post-A8) survive rendering byte-identically — the plain-text renderer may not strip provenance.

## 4. Procedure

Step 0 — Ritual + reading. Fresh clone, HEAD, identity, trio green, prod hash recorded. Read the spec, the E1.5b gate implementation, the current artifact rendering/distribution path, and (read-only) a sample of real approved artifacts spanning early and recent seasons.
Step 1 — Structure design (no code). The §3 structure model as concrete types; the parsing rules; proof-by-walkthrough that the sampled real artifacts parse losslessly; the malformed-artifact surfacing behavior; the consumer-refactor plan naming every touched path. ⛔ Gate 1.
Step 2 — Tests first. The ratified plan implemented red/guard per G2's notes above. ⛔ Gate 2.
Step 3 — Implement + prove. Four steps in order; trio + prove_ci green; byte-identity regeneration proof across all existing artifacts; lint demonstration on a real artifact (firing and clean cases); memo. ⛔ Gate 3 — diff + merge (commit series per convention; STATE line, D-T style).

## 5. Acceptance criteria

Every existing approved artifact regenerates byte-identically through the refactored path · the plain-text rendering of a real artifact contains zero forbidden characters and passes its own lint · every spec §6 prohibition has a green test · the lint is SOFT and standalone (no verifier diff at all in this unit) · trio + prove_ci green · prod hash unchanged · R5 closure is claimed at the implementation layer ONLY if the group-text rendering demonstrably contains no markup artifacts.

## 6. Out of scope

Web rendering against W.2 tokens (frontend unit, later) · print renderer (deferred with the almanac) · any verifier change · any approval-flow change · voice/prompt iteration · Unit A9 · no frontend changes.
