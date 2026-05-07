# OBSERVATIONS — NOTABLE-saturation Step 0b — transform investigation findings

**Date:** 2026-05-06
**Thread:** Standing backlog item 6 — NOTABLE-pass alphabetical lockout investigation
**Brief:** `_observations/session_brief_notable_saturation.md` (`67aca15`)
**Predecessor:** `100ac83` (Step 0a recon memo)

## What this memo is

This is the Step 0b investigation memo. Step 0a (`100ac83`)
documented three findings from recon and named two follow-on
options: (A) run probe against draft pipeline with caveat,
(B) investigate the draft-to-rendered_text transformation.
Step 0b ran Option B. Findings extend Step 0a, not contradict it.

The probe itself (Step 0b's original purpose per the brief)
remains unrun pending direction-choice and scope confirmation
informed by the findings below.

## Finding 4 — The SHAREABLE-marker wrapper is real

`weekly_recap_lifecycle.py:1148-1155` shows the published recap
is composed deterministically:

```
_base_rendered_text.rstrip()
+ "\n\n--- SHAREABLE RECAP ---\n"
+ _narrative_draft
+ "\n--- END SHAREABLE RECAP ---\n"
```

The draft-to-rendered_text transformation is a deterministic
wrap. `_base_rendered_text` is a facts-block prefix produced by
`_render_text_from_recap_runs` (line 994); the LLM's
`_narrative_draft` becomes the SHAREABLE substring; closing
delimiter trails.

For the published W14 2025 recap, the SHAREABLE substring is
1639 characters, the facts-block prefix is the remainder of the
2796-character `rendered_text`. The 860-character delta noted in
Step 0a Finding 3 is fully explained by the facts block plus
delimiters.

This means: for any post-instrumentation publication, the
`rendered_text` substring between SHAREABLE markers should match
exactly one prompt_audit row's `narrative_draft`. The linkage
gap is bridgeable for new recaps.

## Finding 5 — All 2024-2025 publications pre-date prompt_audit instrumentation

W14 2025's APPROVED artifact (id=1027, version=18) was created at
2026-04-09T00:17:57Z and approved at 2026-04-09T00:20:24Z. The
first prompt_audit row for W14 2025 was captured at
2026-04-14T10:09:28Z — five days after publication.

Versions 1-17 of W14 2025 (all the iterations that preceded the
APPROVED v18) were generated before prompt_audit instrumentation
existed. The 17 prompt_audit rows for W14 2025 are all from
regen runs on subsequent versions 19-30, none of which displaced
the APPROVED.

Spot-checking confirmed the same shape across the corpus: every
APPROVED 2024-2025 recap was approved before 2026-04-14 (when
the prompt_audit instrumentation began capturing rows). The
draft that became any given publication was not captured.

This means: the linkage Finding 4 establishes for the post-
instrumentation case is structurally unavailable for everything
already published. There is no prompt_audit row whose
narrative_draft matches any 2024-2025 SHAREABLE substring.

## Finding 6 — narrative_angles_text is not stable across regen

Hashing all 17 prompt_audit rows' `narrative_angles_text` for
W14 2025 produces four distinct values:

- 9d0339 (n=1, 2026-04-14)
- 52c8 (n=6, 2026-04-15 to 2026-04-16 morning)
- e3a6 (n=9, 2026-04-16 afternoon to 2026-04-16 night)
- 55da (n=1, 2026-05-06; this is id=142)

Length comparison: id=27 (oldest) is 2040 chars; id=142 (newest)
is 2093 chars. The text is not invariant under regen.

The most likely explanation: detector code has evolved across
April-May. Recent commits include `cb128d4` (T9-LOSS strength=2
emission) and adjacent section 10 Q1 Step 1 work. Newer
narrative_angles captures reflect newer detector behavior.
Canonical-data evolution (late-arriving roster reconciliations,
FAAB adjustments) may also contribute, but detector evolution is
sufficient to explain the observed variation.

This means: the brief's specimen #1 evidence (id=142's NOTABLE
saturation showing FAAB dominance and STREAK eviction)
characterizes *current* angle-generation behavior on W14 2025
canonical data — not the angle-generation behavior that produced
the published recap on 2026-04-09. Specifically, the T9-LOSS
strength=2 STREAK angle that the brief identifies as evicted in
id=142 cannot have existed in the published recap's prompt
because the T9-LOSS strength=2 emission was added on 2026-05-05.

## Synthesis — what the findings mean for the brief

The brief's NOTABLE-saturation thread targets a real failure
mode: a draft pipeline that, given current detector code, can
saturate the NOTABLE block with FAAB-dominant strength=2 angles
and alphabetically evict a STREAK strength=2 angle. The
mechanism re-derivation in the brief (lines 760-786) is correct.
The cross-franchise candidate scan from `22770d9` (19 tuples *
7 franchises * 16 seasons) is the structural-recurrence evidence
for the league-wide shape.

The findings reframe what the specimen evidence proves:

- id=142 is *not* evidence that the published W14 2025 recap
  lost a STREAK angle — that recap's prompt was generated
  against earlier detector code lacking T9-LOSS strength=2.
- id=142 *is* evidence that, given current detector code, the
  budget loop's alphabetical tiebreak produces NOTABLE
  saturation favoring FAAB over STREAK on a week with this
  shape of canonical data.

These are different claims. The brief writes as if the first;
the probe (if it runs) can only support the second.

## Implications for probe design

The Option A probe (run against current prompt_audit rows) is
structurally sound for characterizing *current* angle-generation
behavior. Bucket counts describe what would happen if drafts
regenerated today; they do not retrospectively measure what
happened in publication.

This is sufficient for direction-choice purposes. The brief's
proposed fix (Direction B rotation hash or Direction C STREAK
reservation, both at line 781) modifies the budget loop. The
probe can characterize the budget loop's current behavior across
the corpus and inform whether rotation, reservation, or neither
is appropriate. The fact that historical publications are not
re-analyzable does not block the design decision for the future
publication pipeline.

The probe should explicitly scope its claim:
"This probe describes draft-pipeline NOTABLE budget behavior
under current detector code and current canonical data. It does
not characterize historical publication behavior."

## Implications for the brief

The brief at `67aca15` does not require revision. The mechanism
analysis stands. The specimen #1 framing should be read as
"demonstration of failure shape under current code" rather than
"evidence that publication X suffered the failure." The
direction-choice question (Direction B vs C) is unaffected by
findings 4-6 — both directions intervene on a future-publication
problem, regardless of whether past publications can be
retrospectively analyzed.

## What this memo does NOT do

- Does not propose changes to source code.
- Does not propose changes to the brief.
- Does not propose changes to the prompt_audit instrumentation
  (e.g., capturing rendered_text alongside narrative_draft).
  That is a separate consideration if/when historical-publication
  analysis becomes important; it does not block the
  NOTABLE-saturation thread.
- Does not propose changes to the deterministic-publication
  pipeline. The SHAREABLE-marker wrapper is a feature, not a
  bug; the linkage Finding 4 establishes is workable for
  forward-looking analysis.

## Disposition

Step 0b's Option B investigation is closed. The Option A probe
remains the brief's intended Step 0b output. With findings 4-6
documented, the probe can run with appropriate scoping caveats.

Steve elects in-session whether to:
1. Run the probe now with the new scoping framing.
2. Pause and resume in a fresh session.
3. Park the thread; the brief at `67aca15` and Step 0a/0b
   memos at `100ac83` and this commit are sufficient context
   for any future activation.

## Anti-drift discipline notes

- Three rounds of investigation in this session each falsified
  a prior round's load-bearing claim. The pattern was not
  rushed-conclusions but slow-falsification: each new check
  revealed something the prior check had assumed. This is
  diagnostic-first discipline working as intended; it produced
  durable findings rather than committed errors.
- The session held to read-only investigation throughout
  Option B. No source-code changes, no probe runs against bad
  premises, no commits except the Step 0a memo and this Step 0b
  memo.
- The convergence pattern (each round added a finding rather
  than overturning a commit) is the safe-mode version of the
  failure pattern that ended yesterday's session. The session
  recognized when each premise broke and revised before
  committing.
