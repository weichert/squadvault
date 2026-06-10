# Narrative Presentation Spec v1.0

Status: Phase 11 Unit E1.5a (Completion Plan Unit 1.7a). Closes the specification
half of finding R5. Authored 2026-06-09, Fable DECIDE session; founder-approved.
Binds the [FROM SPEC] fields of session_brief_e1_5b_formatting_gate_SKELETON.md.

Elections inherited (do not re-litigate):
- D-M: channel-neutral. W.2 has not run; this spec defines structure only.
  W.2's ratified aesthetic later restyles the web rendering (typography,
  spacing, type) without reopening structure. Structure is frozen here.
- D-F: the formatting gate is a standalone deterministic presentation lint.
  The verifier's contract remains purely factual and is untouched.
- Vision Register item 7 governs: presentation is derived-layer; structure is
  specified once and rendered per channel; the facts block is byte-identical
  across all renderings.

## 1. Layer law

Presentation lives at the derived/render layer only. No element of this spec
creates, modifies, or reinterprets a fact. The deterministic facts inputs and
the transactions block are byte-identical inputs to every channel rendering.
Formatting failures flag; they never fabricate and never block on style alone.

## 2. Canonical artifact structure (channel-neutral)

Every weekly recap artifact body (below the YAML frontmatter, which is
lifecycle-owned and out of presentation scope) consists of, in order:

  S1  Title block. Exactly one line:
        PFL Buddies -- Season {season}, Week {week_index}
      (em dash in production; underline treatment is per-channel, section 3)

  S2  Narrative body. Per-matchup sections, lead matchup first, ordered by
      editorial salience. One paragraph per section. Grouping permitted: two
      or more briefly-treated matchups may share one section, provided every
      played matchup is mentioned in exactly one section.

  S3  Standings note. One closing paragraph on the standings picture. May be
      the final paragraph of S2's prose run (current practice, W7 v27) or a
      separated paragraph; it must be present and must be last in the prose.

  S4  Separator. One horizontal-rule line between prose and transactions.

  S5  Transactions block (the distributed deterministic facts block).
      Header line, exactly:  What happened this week:
      followed by one bullet line per transaction ("- " prefix), nothing
      after the final bullet. Quiet weeks: block may be absent entirely;
      a present-but-empty block is a structural defect.

Naming note: "What happened this week:" is the canonical distributed header
(weekly_recap_lifecycle emission; season_html_export BULLETS_MARKER). The
enrichment-side header "What happened (facts)" is a distinct internal label.
No rename in either direction; historical artifacts remain valid.

## 3. Per-channel renderings

All channels render the same S1-S5 structure. Facts content is byte-identical;
only structural dressing differs.

plain_text (channel: group_text_paste_assist) -- the operative channel.
  - S1 title line; setext-style underline line of "=" permitted (reads as a
    plain-text underline; this is the W7 v27 reality and is not markup debris).
  - No markdown markup in prose: no heading hashes, no bold/italic asterisks
    or underscores, no backticks, no link syntax.
  - S4 separator renders as a line of three hyphens.
  - S5 bullets render as "- " lines (native plain-text idiom; permitted).

web_prose (the Clubhouse / season HTML export path).
  - S1 maps to a semantic heading; S2/S3 to paragraphs; S5 to a list element,
    located via the existing BULLETS_MARKER convention.
  - Typography, spacing, and type choices are DEFERRED to W.2 (per D-M).
    Until W.2 ships, the existing export styling stands.

print_almanac (registered, deferred).
  - Same structure, page-safe, no interactive elements. This channel is the
    on-ramp for the print almanac (Deferred-but-registered list). No build
    obligation attaches until that item is scheduled.

## 4. Presentation lint rules (binds E1.5b)

Severity model: SOFT rules flag and surface in the Office review presentation
checklist; they never block approval or publication. Exactly one HARD rule.

  L1 SOFT  Title present: first non-empty body line matches the S1 pattern
           for the artifact's season and week_index.
  L2 HARD  Facts block byte-identity: the span from the header line
           "What happened this week:" through the final "- " bullet line is
           byte-identical to the lifecycle-emitted transactions block for
           this artifact version. Any modification hard-fails pre-approval.
  L3 SOFT  Paragraph bounds: each S2/S3 paragraph contains 2-7 sentences.
  L4 SOFT  Channel markup hygiene: for plain_text, prose contains no "#"
           heading markers, no "**"/"__" emphasis pairs, no backticks, no
           "[text](url)" link syntax. ("=" underline and "- " bullets exempt.)
  L5 SOFT  Structure order: S1 before S2/S3; S4+S5, when present, follow all
           prose; nothing follows the final bullet.

Coverage rule (S2 "every matchup exactly once") is editorially judged at
review, not linted -- linting it would require the lint to consume matchup
facts, coupling presentation to fact semantics against the layer law.

## 5. Revision points

- W.2 ratification: restyles web_prose typography only. Structure (S1-S5) and
  this spec's lint rules are not reopened by W.2.
- NFL Week 1, 2026 season: the first live recap publishes through this
  structure with the E1.5b lint in the publication path. That artifact is the
  acceptance evidence; defects observed there route to a revision memo, not
  silent edits to this spec.
