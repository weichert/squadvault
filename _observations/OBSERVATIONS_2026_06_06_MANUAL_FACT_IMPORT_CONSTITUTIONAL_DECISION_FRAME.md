# OBSERVATIONS 2026-06-06 - Manual Fact Import: Constitutional Decision Frame

**Session type:** Decision-FRAME (founder call pending). No code, no schema change, no
ingest, no fixture mutation. This memo OPENS a constitutional question and records a
recommended resolution for founder ratification. It decides nothing by itself.

**Engine HEAD at framing:** 3e9bfe8 (read-only; this memo is doc-only and SKIPS prove_ci).

**Status:** OPEN - awaiting founder decision on D1-D6 below.

---

## 1. What this is, and what it is not

This memo asks one question: does SquadVault admit facts whose source is a human-attested
artifact (a draft spreadsheet, an FFLM league file, an exported CSV) rather than a live
platform adapter -- and if so, under what conditions?

It is NOT a feature request, NOT an implementation plan, and NOT a fix for the 2021 auction
gap. It touches the governance model -- the frozen layer -- so it is a deliberate founder
decision, framed here and ratified (or amended, or rejected) by the founder, not something
the engine acquires by accretion.

**Explicitly decoupled from 2021.** The 2021 FFLM auction recovery (separate, ongoing) is
what surfaced this question, but the question stands on its own and must be decided on its
own merits. If 2021 prices are never recovered, this decision still matters. If they are
recovered, they become the FIRST calibration instance of whatever is decided here -- not its
justification. Letting a single data point design a general capability is how a substrate
ends up shaped like a fantasy-football workaround.

## 2. Why this is a substrate question, not a fantasy-football one

The platform vision is a universal substrate for niche-aware content, with fantasy football
as the proving ground, not the product. The gardening-club test makes the stakes concrete: a
gardening club has no MFL adapter. Its facts -- show results, member histories, bloom dates
-- are inherently heterogeneous and human-tracked. There is no deterministic API to re-fetch.
For SquadVault to serve any group whose history does not live behind a clean adapter, it
needs a principled way to admit human-attested facts WITHOUT eroding the trust guarantee that
makes the whole thing worth building.

So a manual-import path is not a patch. It is a precondition for the substrate to exist for
non-adapter groups at all. The 2021 hole is simply the smallest, closest instance of the
general problem.

## 3. The reframe that dissolves the apparent conflict

The instinct that manual import "breaks immutability / single canonical source" rests on a
conflation. The constitution's guarantee was never "MFL-derived." Per the Platform Adapter
Contract Card, the guarantee is auditability to a source: adapter facts are trustworthy
because (a) external_id is deterministic from platform-native fields, (b) the raw source
response is preserved in the payload, and (c) identical source data yields identical
envelopes. "MFL-only" is an IMPLEMENTATION property of having exactly one adapter, not a
CONSTITUTIONAL one. The Canonical Operating Constitution says facts are immutable,
append-only, never invented -- it does not say where they originate.

**Key structural finding (this framing session, read-only):** the architecture already
accommodates a second source. The Platform Adapter Contract Card defines the adapter by
behavior, not base class; core/ does not depend on mfl/ (one-way coupling); the canonical
ledger is platform-neutral at the schema level; and the contract already contemplates
additional adapters. A manual import is therefore most honestly framed NOT as a new exception
to governance but as a new adapter under the existing Platform Adapter Contract, whose
"platform" is a retained human-attested artifact.

The one property a manual adapter cannot inherit for free is re-fetchability. A live API can
be re-queried to re-derive a fact. A human artifact cannot. The substitution that preserves
the spirit:

    re-derivability (re-fetch the API)  ->  re-inspectability (re-read the retained artifact)

A manual fact is as trustworthy as an adapter fact IF anyone can audit the parsed rows
against the retained origin artifact and arrive at the same result. That is the whole
admissibility theory in one line.

## 4. The admissibility line (conditions, as a delta over the existing adapter contract)

A live-API adapter already satisfies most of the contract for free. A manual-source adapter
must explicitly carry the parts it cannot get for free. Four conditions:

C1 - Immutable, load-bearing provenance class. Every manual fact is stamped at ingest as
   human-attested, not adapter-derived. The stamp lives in external_source (e.g.
   "MANUAL:FFLM-2021" rather than "MFL"), is never strippable, and is visible to every
   downstream consumer -- the Writer's Room and, critically, the verifier. Provenance is
   load-bearing, not a soft tag. This is the condition that prevents manual data masquerading
   as adapter-grade.

C2 - Retained source artifact. The origin -- the FFLM file, the spreadsheet, the CSV, the
   screenshot -- is stored alongside the parsed rows, in or referenced by the payload, NOT
   truncated. (The existing contract permits truncation of API responses because the API can
   be re-fetched; a human artifact cannot, so for the manual class retention is mandatory and
   complete.) Typed-in numbers with no retained source DO NOT clear the bar.

C3 - Attributed human approval as the ingest act. For adapter facts, the API is the authority
   and "humans approve" attaches to Writer's Room OUTPUT. For a manual fact, the IMPORT itself
   creates fact, so it requires its own approval gate: who imported, when, against which
   artifact -- logged. This reuses the approval shape already built for the founding ceremony.

C4 - Partial truth, never gap-filling. If 8 of 10 franchises' prices are legible in the
   artifact, 8 rows import and the other 2 stay absent. No interpolation, no "typical" value,
   no guessing. Silence over speculation survives intact at the import layer.

Determinism still binds: re-importing the same artifact must produce identical envelopes
(external_id deterministic from artifact-native fields -- franchise + player + price + season
-- never from SquadVault-internal state). This is the existing contract's determinism rule,
re-pointed from "platform-native" to "artifact-native."

## 5. Verifier disposition: a third path

The DRAFT_AUCTION_DOLLAR category (Category 13, S4 tiering in the 2026-06-06 verifier remedy
decision) today has two dispositions: HARD when a voiced figure contradicts re-derived ground
truth or fabricates against a covered scope; SOFT / flag-for-review when there is NO coverage
(e.g. the 2021 gap), preserving silence-over-speculation by surfacing to the commissioner
rather than asserting wrongness.

A manual fact needs a THIRD disposition, derived from C1's provenance class:

    adapter-derived coverage  ->  HARD re-derive (as today)
    no coverage               ->  SOFT / surface (as today)
    manual-attested coverage  ->  re-derive against the imported rows (fabrication relative to
                                  the IMPORT is still caught), but disposition as
                                  "human-attested, unverifiable against a live source" --
                                  NOT asserted as externally correct, NOT silently equated
                                  with adapter-grade ground truth.

The verifier thus still catches a recap that misquotes the imported numbers, while never
laundering a human-attested figure into platform-grade certainty. The provenance class flows
all the way to the verifier's verdict.

## 6. The hazard, stated plainly

This is the single most dangerous capability SquadVault could add. It is the one path where:
- a typo becomes an immutable, append-only "fact," and
- human data could masquerade as adapter-grade if provenance were cosmetic.

C1 (load-bearing provenance) and C2 (retained artifact) exist precisely to make both
impossible. If either is weakened to a convenience tag, the capability should not ship. The
hazard is the reason this is a founder call and not an implementation detail.

## 7. Decisions for founder ratification

D1 - Admit the manual-source adapter class at all?
   (a) Yes -- as a new adapter under the existing Platform Adapter Contract, conditions C1-C4
       binding. [recommended]
   (b) No -- adapter facts remain the only admissible facts; non-adapter groups and the 2021
       prices are permanently out of scope. Honest and conservative, but forecloses the
       substrate vision for non-adapter groups.
   (c) Defer until the substrate is pursued beyond fantasy football in earnest.

D2 - Provenance mechanism (C1). (a) Encode in external_source string [recommended -- reuses an
   existing field, visible everywhere]; (b) new dedicated column; (c) both.

D3 - Artifact retention (C2). (a) Store artifact bytes in payload [recommended for small
   artifacts]; (b) store a reference + hash with the artifact in a retained store; (c)
   hash-only [rejected -- defeats re-inspectability].

D4 - Approval gate (C3). (a) Reuse founding-ceremony approval shape [recommended]; (b) new
   manual-import approval flow.

D5 - Verifier third path (section 5). (a) Add the manual-attested disposition [recommended if
   D1=a]; (b) treat manual coverage as no-coverage / SOFT [simpler, but loses fabrication-
   against-import detection].

D6 - Sequencing. (a) Ratify this frame, then author a Manual Source Adapter Contract addendum
   (subordinate to the Platform Adapter Contract Card) BEFORE any code, then exercise it first
   on a safe calibration case [recommended]; (b) other.

**Recommendation in one line:** D1(a), D2(a), D3(a), D4(a), D5(a), D6(a) -- admit the class as
a contract-conforming adapter with load-bearing provenance and mandatory artifact retention;
write the addendum before code; calibrate on a safe first case.

## 8. Why 2021 is the ideal first calibration case (if recovered) -- and a bad reason to pre-build

If the FFLM prices are recovered, 2021 is an unusually SAFE first exercise: the 2021 rosters
are already adapter-grade in MFL (the price-free LOAD_ROSTERS bulk loads). Imported prices
attach to players already verified on each franchise's roster -- so half of each fact has an
integrity anchor, and the manual half (the price) is cross-checkable against the known roster.
That is close to a best-case calibration instance. It remains a BAD reason to pre-build:
calibrate the decided design on it; do not let it author the design.

## 9. Scope boundaries (non-goals)

- No code, no schema change, no ingest in this memo. Frame only.
- No decision is made by this memo; D1-D6 await the founder.
- Decoupled from 2021 recovery: this stands whether or not prices are found.
- If admitted, the Manual Source Adapter Contract addendum is the next artifact, BEFORE code.
- Architecture and layer structure unchanged: this proposes an adapter UNDER the existing
  Platform Adapter Contract, not a new layer and not a governance carve-out.

## 10. Constitution note

This frame proposes nothing that modifies immutability, append-only, narratives-derived, or
silence-over-speculation. It re-reads "single canonical source" as "auditable to a source"
(re-derivability OR re-inspectability) and locates the manual path inside the existing
Platform Adapter Contract. Because it nonetheless touches how facts enter the ledger -- the
governance boundary -- it is a founder ratification, recorded append-only, superseding
nothing.

## 11. State at framing

- Engine HEAD 3e9bfe8, read-only this session. This memo is the only artifact.
- Doc-only commit when landed: _observations/, ASCII subject, SKIP prove_ci, one topic.
- Next step gated on founder: ratify / amend / reject D1-D6. If admitted, author the Manual
  Source Adapter Contract addendum BEFORE any code.

---

Predecessor context (read this session, not re-derived here): Platform Adapter Contract Card
v1.0; Canonicalization Semantics Addendum v1.0; OBSERVATIONS_2026_06_06_VERIFIER_DRAFT_
AUCTION_DOLLAR_GAP_REMEDY_DECISION.md (S4 tiering); the 2021 DRAFT_PICK gap thread
(3a35308 / 8bc5ceb / 3e9bfe8) as the surfacing instance, not the driver.
