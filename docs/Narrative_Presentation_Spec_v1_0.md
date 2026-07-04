# SquadVault Narrative Presentation Spec v1.0 (Unit 1.7a)

Status: CANONICAL upon landing. Ratified: P1–P6, founder, 2026-07-03/04. Implements: Completion Plan Unit 1.7a; closes R5 at the spec layer. Implementation: Unit 1.7b (separate brief).

## 1. Purpose and lineage

This spec defines how an approved weekly recap artifact is presented per distribution channel. It exists because the R5 gap was never the facts block — the E1.5b formatting gate ships facts-block byte-identity and only that — but the published narrative: artifacts distributed via group-text paste with raw markup rendering as literal characters, no per-matchup structure, no channel-appropriate form. Any future reconciliation reading "R5 closed" against E1.5b alone is misreading; R5 closes when this spec's renderings ship (1.7b).

## 2. The invariance law

Structure is defined once, at the derived/render layer. Each channel rendering is a pure function of that structure. The deterministic facts block is byte-identical across every channel. Renderers may clothe content — typography, spacing, dividers — and may never add, remove, reorder, or rephrase it. Presentation is derived-layer work: fully safe, facts untouched. (Vision Register item 7, operationalized.)

## 3. Canonical artifact structure

Ordered sections of a weekly recap artifact:

- Masthead — PFL BUDDIES — WEEK {N} — {SEASON} (all caps, em-dash separators in structure; each channel renders its own divider form).
- Title block — the artifact's title as approved.
- Narrative lede — the approved creative text, verbatim as approved. Never regenerated or trimmed at render time.
- Per-matchup sections — one per matchup in the approved artifact, each with a matchup heading (team names and final score, drawn from structure, not re-derived) and its approved body text.
- Transactions block — the approved transaction content for the window.
- Standings note — the approved standings text.
- Facts block — the deterministic facts block, byte-identical, always last.

The silence rule: a section with no approved content is omitted entirely — no headers over nothing, no "Transactions: none," no placeholders. Silence over filler. Only the masthead, title, and facts block are unconditional; everything between appears only if the approved artifact contains it.

## 4. Channel renderings

### 4.1 Plain-text / group-text (the distribution channel; specified rigorously)

- Zero markup. No asterisks, underscores, hash marks, backticks, angle brackets, or any character sequence that a messaging client renders literally or mangles. The W7 v27 failure — markdown artifacts in the league text — is the defect class this rendering exists to eliminate; the 1.7b lint enforces it mechanically.
- Structure through whitespace and case. Masthead in caps as its own line. Section headings in caps on their own line, one blank line above, none below. Body text as plain sentences and paragraphs. A single blank line between sections.
- Dividers: at most a single line of hyphens (----) between the narrative body and the facts block; nowhere else. No box-drawing, no emoji dividers.
- No manual line-wrapping. Paragraphs are single logical lines; the client wraps. No hard breaks inside sentences.
- Emoji policy: none. The league's voice is the words.
- Scores and numbers exactly as the facts block renders them — same precision, same form, no re-rounding.

### 4.2 Web (consumes W.2 by reference — ratified D-M)

The web rendering maps structure to the W.2 design language's named type roles; it does not re-specify faces, sizes, or colors. Mapping: masthead → the mono eyebrow/label register (as on the splash and trophy-room surfaces) · title → the ceremonial serif display register · section headings → the secondary heading register · body → the body register · facts block → the mono register, visually set apart as a record, never restyled as prose. One source of aesthetic truth: if W.2's tokens evolve, the web rendering follows without a spec change. The trust bar remains part of the artifact per the standing Design Brief ruling.

### 4.3 Print / almanac-ready (constraints only in v1)

Structure must survive pagination: no element depends on interactivity, hover, or color to carry meaning; section boundaries are honest page-break points; the facts block may not be split from its heading. A full print rendering is deferred with the registered almanac product; this section exists so nothing in 1.7b forecloses it.

## 5. The facts block

Produced upstream, deterministic, verifier-governed — this spec inherits it and adds only placement (always last) and the byte-identity guarantee across channels. No rendering may reformat, re-wrap, re-order, or elide any part of it. The E1.5b gate continues to enforce byte-identity; this spec makes the guarantee cross-channel.

## 6. What renderers may never do

Add content (including "helpful" labels over empty sections) · remove or truncate approved text · reorder sections or matchups · rephrase, correct, or normalize approved prose · re-derive any number, name, or score from data (renderers read structure, never the database) · vary the facts block in any byte · emit channel-inappropriate markup · fabricate a rendering for an artifact that fails structural parsing — a malformed artifact is surfaced, not repaired (silence over speculation, presentation edition).

## 7. Consumption notes for Unit 1.7b

1.7b implements per the proven four-step playbook: pre-render the canonical structure at the data layer in render/; refactor consumers to read it; add the deterministic presentation lint (masthead present, title present, facts block intact and byte-identical, no forbidden markup for the target channel, paragraph-length bounds, no orphaned headers) running alongside the verifier pre-approval and surfaced as a presentation checklist in the Office review UI. Per ratified D-F the lint is standalone and SOFT-tier — formatting failures flag for human review, never fabricate and never block on ambiguity — and the verifier's contract stays purely factual. Structural rules live in this spec and the lint, never in the verifier.
