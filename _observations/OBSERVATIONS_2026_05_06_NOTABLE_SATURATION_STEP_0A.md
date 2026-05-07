# OBSERVATIONS — NOTABLE-saturation Step 0a — recon findings and probe scope reconsideration

**Date:** 2026-05-06
**Thread:** Standing backlog item 6 — NOTABLE-pass alphabetical lockout investigation
**Brief:** `_observations/session_brief_notable_saturation.md` (`67aca15`)
**Predecessor:** `1e2c0f5` (labeling correction memo)

## What this memo is

This is a Step 0a recon-output memo, written in lieu of a probe
result. The probe was not run because recon surfaced a scope
question that should be settled before probe design proceeds.

## What the recon found

Recon ran against `.local_squadvault.sqlite` to design the
NOTABLE-saturation probe per brief section "Step 0 — Diagnostic
harness or new probe." Three findings emerged in sequence:

### Finding 1 — id=142 is not the W14 2025 APPROVED recap

The brief's specimen #1 (id=142) was assumed to represent
the W14 2025 published recap. Recon found:

- prompt_audit.id=142 was captured at 2026-05-06T18:22:15Z
  (today).
- The W14 2025 APPROVED artifact (recap_artifacts.id=1027,
  version=18) was approved before id=142 existed; the
  associated prompt_audit rows for that week run from
  2026-04-14 through 2026-04-16.
- id=142 is the most recent draft regen, likely produced by
  yesterday's section 10 Q1 Step 1 thread work.

The brief's specimen analysis (6 NOTABLE entries, all FAAB,
STREAK evicted) describes a 2026-05-06 draft, not the published
W14 2025 recap.

### Finding 2 — prompt_audit to recap_artifacts has no clean linkage

recap_artifacts is keyed on (league_id, season, week_index,
artifact_type, version) with no foreign key to prompt_audit.
selection_fingerprint is an opaque hash that does not appear
on prompt_audit rows. There is no recap_artifact_id or
equivalent pointer column on prompt_audit.

To identify the prompt_audit row that produced a given APPROVED
artifact, the only available signal is text comparison between
prompt_audit.narrative_draft and recap_artifacts.rendered_text.

### Finding 3 — narrative_draft never matches rendered_text

Comparison across all 2024-2025 (season, week) tuples
(33 weeks, 130+ prompt_audit rows): zero exact matches between
narrative_draft and rendered_text.

For W14 2025 specifically: 17 prompt_audit rows, draft lengths
1456-1936, rendered_text length 2796. The published recap is
roughly 860 characters longer than any individual draft and
shares no draft's content exactly.

This implies the draft to rendered_text transformation is
non-trivial. The publishing pipeline appears to add or transform
content between the LLM's narrative_draft and the APPROVED
artifact's rendered_text (likely creative-layer or
post-processing additions; not investigated in this recon).

## What this means for the brief's probe

The brief's probe (section "Step 0 — Diagnostic harness or
new probe") was scoped to classify (season, week) tuples by
NOTABLE saturation buckets, with the implicit assumption that
prompt_audit rows describe the published recap pipeline.

Findings 1-3 invalidate that assumption. The probe can still
be run, but its findings would describe the draft pipeline,
not what readers actually saw. Concretely:

- A prompt_audit row showing NOTABLE saturation tells us a
  draft produced a saturated NOTABLE block. Whether that
  saturation persisted into the APPROVED recap is unknown
  without bridging the linkage gap.
- The brief's "editorial density loss" framing assumes the
  draft pipeline's NOTABLE block is what shapes the published
  recap. If the publishing transformation adds, removes, or
  rewrites NOTABLE-equivalent content, the eviction at draft
  layer may not survive to publication, or saturation may
  emerge from sources outside prompt_audit.

## What this does NOT mean

- The mechanism described in the brief (alphabetical tiebreak
  in the strength=2 budget loop at line 781) is real and
  remains valid. The code at lines 760-786 demonstrably
  implements it.
- The cross-franchise candidate scan from 22770d9 is not
  invalidated; it describes streak-shape arithmetic across
  the league's history independent of recap publication.
- The fabrication-prevention work in section 10 Q1 is not
  affected; STREAK's verifier surface (Cat 3/Cat 3c) operates
  on draft prose, which prompt_audit captures cleanly.
- Original Bug 1 status is unchanged.

## Two follow-on options

### Option A — Run probe against draft pipeline; caveat results

The brief's probe runs against all prompt_audit rows. Bucket
counts describe draft-pipeline NOTABLE saturation. Findings are
useful for understanding budget-loop behavior at the level the
brief's proposed fix (Direction B or C, both at line 781) would
intervene. Direction choice is reasonable from this evidence
because the fix lives in the same pipeline layer as prompt_audit
captures.

The caveat: probe findings do not validate the brief's "loss of
editorial density in published recaps" framing, only "loss of
draft-layer NOTABLE entries."

### Option B — Investigate the draft to rendered_text transformation

If the gap between narrative_draft and rendered_text is
recoverable (e.g., a deterministic post-processing step that
prompt_audit doesn't capture), Option A becomes structurally
sound. If the gap is unrecoverable (e.g., creative-layer
generates content from sources outside prompt_audit), the brief's
NOTABLE-saturation thread requires either new instrumentation
(capturing post-transform recap state in prompt_audit-equivalent
form) or a different evidence pipeline.

This investigation is read-only: locate the
narrative_draft to rendered_text transformation in source,
characterize what it does, decide whether prompt_audit linkage
to APPROVED artifacts is a fixable gap or structural.

## Disposition

Steve elects in-session whether to:

1. Pause both threads pending fresh-session investigation.
2. Continue with Option B (transform investigation) this session.
3. Continue with Option A (degraded probe) this session.
4. Park NOTABLE-saturation thread; the brief at 67aca15
   stays valid as scope, but Step 0 is parked until linkage is
   resolved.

This memo is the closure of Step 0a (recon). Step 0b (probe
run) is paused pending disposition.

## Anti-drift discipline notes

- Mechanism re-derivation against current data caught the
  specimen-vs-published distinction. The brief author had
  access to id=142 in session memory and used it as specimen
  evidence; recon dating revealed id=142 was generated after
  the W14 2025 recap was approved.
- Read the prose before proposing a fix (per brief discipline
  #3): the prose-reading step revealed the linkage gap that
  the brief's mechanism re-derivation alone did not surface.
- This memo does not propose changes to the brief, the active
  thread, or any source code. The brief at 67aca15 remains
  the scope-of-record; this memo records what Step 0a found
  and what Step 0b cannot yet do.
