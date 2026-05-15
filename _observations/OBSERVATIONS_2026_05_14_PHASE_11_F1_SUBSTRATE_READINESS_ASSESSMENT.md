# Phase 11 F1 (Rivalry Chronicle) -- Substrate-Readiness Assessment

**Date:** 2026-05-14
**HEAD at memo-write:** `6ae691a` (E3 Phase B: finding memo + convenience shim)
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**Output:** Empirical substrate-readiness assessment for F1. The Roadmap at `ba8b58a`
section 4.5 estimated ~6-8 sessions of substrate-plus-composition work. This assessment
finds the arc is approximately 85% complete with two items remaining. The arc opens with
this memo and targets completion in the same session.

---

## 1. What the Roadmap estimated

Per `ba8b58a` section 4.5:

| Component | Estimate |
|---|---|
| Multi-season window infrastructure | 1 session |
| Chronicle facts-block renderer | 0.5-1 session |
| Chronicle creative-layer prompt construction | 1 session |
| Chronicle trace-block helper | 0.25-0.5 session |
| Chronicle audit/persistence schema decision + migration | 0.5 session |
| Chronicle composition lifecycle | 1.5-2 sessions |
| Chronicle verifier | 1 session |
| Integration, end-to-end testing, contract-compliance probe | 0.5-1 session |
| **Total** | **6-8 sessions** |

The estimate was generated before the chronicle pipeline was built. Direct substrate
probe at HEAD `6ae691a` finds most of this work already complete.

---

## 2. Empirical substrate state (direct probe findings)

### 2.1 Components confirmed COMPLETE

**`src/squadvault/chronicle/` module (6 source files):**
- `input_contract_v1.py` -- input validation, week normalization, missing-weeks policy
- `matchup_facts_v1.py` -- `query_head_to_head_matchups_v1()` querying canonical events
  for a team pair; `facts_block_hash_v1()` for deterministic trace
- `approved_recap_refs_v1.py` -- loads APPROVED recap refs for chronicle generation
- `generate_rivalry_chronicle_v1.py` -- full contract-compliant generation path (team pair
  -> facts block -> optional narrative -> trace block -> disclosures) + legacy path
- `format_rivalry_chronicle_v1.py` -- `render_rivalry_chronicle_contract_v1()` rendering
  all four contract-mandated sections (Header, Facts Block, Narrative, Trace, Disclosures)
- `persist_rivalry_chronicle_v1.py` -- DRAFT state machine, idempotency via fingerprint,
  versioning, schema-resilient insert

**`src/squadvault/ai/creative_layer_rivalry_v1.py`:**
- EAL-governed narrative drafting with conservative MODERATE_CONFIDENCE_ONLY default
- Silent fallback on any failure (no API key, import error, API error)
- temperature=0 for determinism; 2-5 sentence constraint; no emotional attribution

**Consumers:**
- `src/squadvault/consumers/rivalry_chronicle_generate_v1.py` -- full CLI with
  `--team-a-id`, `--team-b-id`, `--weeks` / `--week-range` / `--start-week/--end-week`,
  `--missing-weeks-policy`, `--out`
- `src/squadvault/consumers/rivalry_chronicle_approve_v1.py` -- DRAFT -> APPROVED
  lifecycle with idempotency, empty-text guard, signature-resilient approve primitive

**Tests:** 27 passing, 1 skipped across 11 test files. Coverage includes: contract
compliance, determinism, persistence, governance alignment, input contract, approval
idempotency, artifact type persistence, format rendering, creative layer, competitive
rivalry, tenure rivalry angles.

**Prove script:** `scripts/prove_rivalry_chronicle_end_to_end_v1.sh` -- generate ->
approve -> export end-to-end proof.

**Live DB artifacts:** 2 chronicle rows in `recap_artifacts`:
- Season 2024, week_index 17, version 1, state APPROVED (Stu's Crew vs Paradis'
  Playmakers, W1-17, 3 head-to-head matchups found, correct structure)
- Season 2024, week_index 18, version 1, state DRAFT

**The approved artifact structure is correct:** Header, H2H Results (facts block with
canonical event fingerprints), Chronicle (2-sentence EAL-governed narrative), Trace
(team IDs, weeks, fingerprints, facts_block_hash), Disclosures. The contract card's
four output sections are all present.

### 2.2 Components confirmed MISSING

**Chronicle verifier:** `src/squadvault/core/recaps/verification/recap_verifier_v1.py`
exists but has no `RIVALRY_CHRONICLE_V1` coverage. The governance model requires a
verifier before F1 is admissible: human approval is the hard gate, but the verifier is
the automated pre-approval quality check (analogous to how `recap_verifier_v1.py`
catches score errors, banned phrases, and record-claim anchoring violations before a
weekly recap is approved). **This is the primary remaining gap.**

**Convenience shim:** No `scripts/generate_rivalry_chronicle.py` equivalent. The
commissioner must specify full flags to the consumer. A shim pre-filling PFL Buddies
defaults (`--db`, `--league-id`) reduces invocation to `--team-a-id`, `--team-b-id`,
`--season`, and week selection.

### 2.3 Components deferred to v1.1

**Multi-season capability:** `query_head_to_head_matchups_v1` is single-season only.
Multi-season rivalry (all 17 seasons of head-to-head history) is a genuine product
improvement but not required for v1. A single-season chronicle covering W1-W17/18 is
meaningful output (3 head-to-head matchups in 2024 is a real rivalry). Multi-season
deferred to v1.1 arc.

---

## 3. Arc plan

**Remaining work (this session):**

1. **Chronicle verifier** -- `src/squadvault/core/recaps/verification/chronicle_verifier_v1.py`
   Checks: facts_block_hash integrity; no banned phrases in narrative; score accuracy
   (any score cited in narrative matches the facts block); trace block completeness.
   Analogous to `recap_verifier_v1.py` but scoped to RIVALRY_CHRONICLE_V1 output.

2. **Convenience shim** -- `scripts/generate_rivalry_chronicle.py`
   Pre-fills `--db .local_squadvault.sqlite` and `--league-id 70985`. Standard
   invocation: `./scripts/py scripts/generate_rivalry_chronicle.py --team-a-id 0001
   --team-b-id 0002 --season 2025 --weeks 1-18`.

**Not in scope this session:** multi-season capability (v1.1); Map registration
(F1 surface specification is the proper registration path, upstream of which is the
per-surface constitutional memo chain, upstream of which is this substrate-readiness
arc completion).

---

## 4. Confidence labeling

### 4.1 Highest-confidence claims

- The generation, persistence, and approval pipeline is complete and tested. The
  approved artifact in the live DB has the correct contract structure. (section 2.1)
- The chronicle verifier is absent. This is a governance gap, not a quality gap in
  the existing code. (section 2.2)
- Multi-season is not required for v1. Single-season chronicles are meaningful output.
  (section 2.3)

### 4.2 Medium-high confidence claims

- The prove script's contract compliance check (section 2.1) has been patched
  extensively and has some code quality issues (multiple SV_PATCH comments, bypassed
  legacy export block). It works end-to-end but is not clean production code. The
  convenience shim supersedes it for the standard workflow.
- The Roadmap estimate of 6-8 sessions significantly overestimated the remaining work
  because the pipeline was already under construction when the estimate was made.

### 4.3 Claims this memo deliberately does not make

- No characterization of the DRAFT artifact at week_index 18. Its content is not
  reviewed here.
- No prescription of the chronicle verifier's exact rule set. That is the verifier
  session's call, informed by the contract card's invariants.
- No pre-commitment on F1 surface specification timing. This arc completes the
  substrate-readiness gate; the surface specification chain is a separate decision.

---

## 5. Cross-references

- `ba8b58a` -- Phase 11 Surface Roadmap (section 4.5 substrate-readiness arc estimate)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- Tier 2 (the contract the verifier enforces)
- `src/squadvault/chronicle/` -- complete pipeline (section 2.1)
- `src/squadvault/core/recaps/verification/recap_verifier_v1.py` -- weekly recap verifier
  (structural precedent for the chronicle verifier)
- `6ae691a` -- HEAD at this session (E3 Phase B complete; E-cluster exhausted)

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_F1_SUBSTRATE_READINESS_ASSESSMENT.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Chronicle verifier implementation + convenience shim. Two commits.
