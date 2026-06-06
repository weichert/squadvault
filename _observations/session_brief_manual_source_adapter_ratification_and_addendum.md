# Session Brief — Manual Source Adapter: Founder Ratification + Contract Addendum

**Date prepared:** 2026-06-06
**Session type:** Founder decision (ratify D1-D6 from the decision frame) + IF admitted,
author the Manual Source Adapter Contract addendum. Doc-authoring only; doc-only commits.
**No code, no schema change, no ingest** this session (frame's D6 sequencing: addendum
precedes code).
**Engine HEAD at handoff:** the commit that lands
`OBSERVATIONS_2026_06_06_MANUAL_FACT_IMPORT_CONSTITUTIONAL_DECISION_FRAME.md`
(HEAD was `3e9bfe8` before that memo; CONFIRM in verify-first -- the frame memo was authored
last session but landed by the founder separately).
**Repo:** `weichert/squadvault` -- local `~/projects/squadvault-ingest-fresh`.

---

## Why this session exists

The prior session opened the manual-fact-import question as a constitutional **decision
frame** (the memo named above). The frame's spine, established and not to be re-derived:

- A manual import is most honestly framed as **a new adapter UNDER the existing Platform
  Adapter Contract**, whose "platform" is a retained human-attested artifact -- NOT a
  governance carve-out and NOT a new layer.
- The constitution's guarantee was always **auditability to a source**, not "MFL-derived."
  The one thing a human artifact cannot inherit for free is re-fetchability; the frame
  substitutes **re-inspectability** (re-read the retained artifact and arrive at the same
  rows).
- Four binding admissibility conditions: **C1** load-bearing immutable provenance class
  (in `external_source`, never strippable, visible to the verifier); **C2** complete,
  untruncated retained source artifact; **C3** attributed human approval as the import act
  (reusing the founding-ceremony shape); **C4** partial truth, never gap-filling.
- The verifier gets a **third disposition** beyond the Category 13 S4 HARD/SOFT tiering:
  manual-attested coverage -> re-derive against the imported rows (catch misquotes) but never
  launder into platform-grade certainty.
- The frame DECIDES NOTHING. It opens **D1-D6** for the founder.

This session is where the founder decides D1-D6 and, if the class is admitted, where C1-C4
become **binding spec** in a Manual Source Adapter Contract addendum subordinate to the
Platform Adapter Contract Card.

---

## Verify-first (mandatory)

The stale-backlog hazard is live here: this brief assumes the frame memo landed. Confirm it
on disk before building on it.

    git log --oneline -6            # confirm HEAD; the frame memo's commit should be at/near top
    git status                      # tree clean
    grep -rln "MANUAL_FACT_IMPORT" _observations/   # frame memo present?

Then READ, in order, before any authoring:
1. `_observations/OBSERVATIONS_2026_06_06_MANUAL_FACT_IMPORT_CONSTITUTIONAL_DECISION_FRAME.md`
   (the decisions and the prior recommendation).
2. `Platform_Adapter_Contract_Card_v1_0` (the parent contract this addendum is subordinate
   to -- match its structure and vocabulary: discover/ingest behavior contract, deterministic
   external_id from source-native fields, external_source declaration, payload source
   retention, determinism and auditability).
3. The Category 13 S4 tiering in
   `OBSERVATIONS_2026_06_06_VERIFIER_DRAFT_AUCTION_DOLLAR_GAP_REMEDY_DECISION.md` (the
   precedent the verifier third path extends).

Do not trust this brief's summary over the on-disk frame memo.

---

## Step 1 -- Founder ratification of D1-D6 (STOP-AND-REPORT before authoring)

Read the frame's D1-D6. Prior-session recommendation was D1(a) through D6(a): admit the
class as a contract-conforming adapter, provenance in `external_source`, artifact bytes in
payload, founding-ceremony approval shape, verifier third path, addendum-before-code
sequencing.

The founder ratifies, amends, or rejects EACH. **Surface the chosen options and stop** before
authoring -- the addendum's content is a direct function of D2 (provenance mechanism), D3
(retention mechanism), D4 (approval gate), and D5 (verifier path). Authoring against
unconfirmed options is the failure mode.

Note D1 is a real fork: D1(b) "no -- adapter facts only" is a coherent, conservative choice
that forecloses non-adapter groups and is NOT a wrong answer. Do not steer; record the call.

---

## Step 2 -- Deliverable (conditional on D1)

**If D1(a) -- admit the class:** author the **Manual Source Adapter Contract addendum**,
subordinate to the Platform Adapter Contract Card. It must turn C1-C4 from frame language
into binding spec:

- C1 provenance: the exact `external_source` encoding (per D2), the non-strippability
  requirement, and the rule that it propagates to every consumer including the verifier.
- C2 retention: the artifact storage mechanism (per D3), and the hard rule that retention is
  complete and untruncated for this class (unlike the API-response truncation the parent
  contract permits, because the artifact cannot be re-fetched).
- C3 approval: the import-as-fact-creating-act approval gate (per D4) -- who/when/which
  artifact, logged.
- C4 partial truth: legible rows import, illegible stay absent, no interpolation.
- Determinism: external_id deterministic from **artifact-native** fields (e.g. season +
  franchise + player + price), never SquadVault-internal state -- the parent contract's rule
  re-pointed.
- Verifier disposition (per D5): the manual-attested third path as binding behavior.
- Declared supported categories and explicit non-goals (no live discovery; no re-fetch; one
  artifact = one import event).

Doc-only commit, `_observations/` or `docs/` per the documentation map's placement for
contract addenda (check the map; the Platform Adapter Contract Card's neighbors are the
precedent). ASCII subject, one topic, SKIP `prove_ci`. **No code this session.**

**If D1(b) or D1(c):** a short closure/deferral memo recording the decision and its rationale;
no addendum. Doc-only.

---

## Parked dependency -- the 2021 thread (NOT this session's primary work)

2021 is now **fully diagnosed** and does not need re-investigation: off-platform FFLM auction;
only the resulting rosters were commissioner-bulk-loaded into MFL (price-free LOAD_ROSTERS,
Aug 13 2021); the auction PRICES were never entered into MFL at all -- confirmed by drilling
the actual MFL transaction records (no dollar values present). So 3e9bfe8's C4 ("no auction /
correct-by-design") is wrong, and the brief's "ingest data loss" is the wrong mechanism; the
truth is an off-platform auction whose prices never reached the platform.

The single **supersession memo** correcting 3e9bfe8 (and folding in `8bc5ceb`, reconciling
the stale ROADMAP §7.3 entry) is STILL UNWRITTEN, held per the original 2021 brief's
"recover-first / do not amend 3e9bfe8 twice." The founder is tracking down the off-platform
source (likely an FFLM file held by a specific person) -- **no clock**.

OPTIONAL micro-decision this session may take (only if there's appetite; it is not the point
of the session): write the 2021 supersession memo NOW vs keep holding. The tradeoff has
shifted since the original brief -- the **cause** is now definitively established and
independent of recovery; only the **recoverability disposition** (permanent-loss vs
recoverable-pending-admissibility) depends on the founder's search. A future successful
recovery would be a separate event (an admitted import under the new addendum), not a second
amendment of 3e9bfe8 -- so writing the cause-correction now would not violate "do not amend
twice." If the founder prefers, keep holding for one clean memo. Recommend deciding this
explicitly rather than letting it drift uncorrected in the record indefinitely.

---

## Scope boundaries (non-goals)

- **No code, no schema migration, no ingest** -- D6 sequencing puts the addendum before code.
- **No 2021 data import** -- gated on recovery AND, if non-MFL, the admissibility decision the
  addendum will govern. The addendum must be designed for the general case, not shaped around
  2021.
- The addendum is **subordinate spec under the Platform Adapter Contract Card** -- not a new
  architectural layer, not a governance carve-out. Architecture stays frozen.
- No analytics, optimization, engagement loops, or prediction (as always).
- Verify the frame memo landed before authoring on top of it.

---

## Stop-and-report checkpoints

- **After verify-first:** confirm the frame memo is committed and report HEAD + clean tree.
- **After D1-D6 ratification:** report the chosen options and STOP before authoring -- the
  addendum content depends on D2-D5.

---

## One-line kickoff for the next session

> Ratify the manual-source-adapter decision frame (D1-D6) authored last session, then -- if
> D1=admit -- author the Manual Source Adapter Contract addendum (subordinate to the Platform
> Adapter Contract Card) turning C1-C4 into binding spec, addendum-before-code. Verify the
> frame memo landed FIRST; stop and report the ratified options before authoring. Doc-only,
> no code. 2021 supersession memo remains parked pending recovery (optional micro-decision:
> write the cause-correction now vs keep holding).
