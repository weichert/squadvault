# OBSERVATIONS_2026_05_02 — docs-integrity gate resolution: Position 3 selected (surgical retirement)

**Predecessor:** `_observations/OBSERVATIONS_2026_05_02_DOCS_INTEGRITY_GATE_FINDING.md` (74f58c8) — the finding memo that surfaced this question and named three coherent interpretations.

**Stated purpose:** select Interpretation 3 (the gate has a stale assumption) as the architecturally correct resolution to the docs-integrity gate failure. Specify the resolution as Position-3-style surgical retirement of `gate_ci_index_coverage` from `scripts/check_docs_integrity_v1.py`. Explain why Interpretations 1 and 2 were rejected. Frame the follow-on refactor session as the operational-completion deliverable.

This memo resolves the question. It does not execute the surgical edit. The docs-integrity gate continues to fail at `prove_ci.sh` rc=1 until a separate session removes the dormant invocation; the failure is now an explicitly-recorded transitional condition with a known resolution path, paralleling today's H7 Cat B sequence.

## The question being resolved

From the finding memo's three interpretations:

> **Interpretation 1** — the index's scope should expand to include invariant docs and proof runners (gate is correct).
>
> **Interpretation 2** — the gate is checking the wrong file (index is correct).
>
> **Interpretation 3** — the gate has a bug or stale assumption (gate was written against a wider scope that the index used to have but no longer does).

The doc-read this session establishes which interpretation the canonical history supports.

## Canonical archaeology

Three documents tell the story.

### Phase 7.8 — the deliberate scope reduction

From `_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_RETIRED.md`:

> Phase 7.8 (`0faf0c0`, 2026-03-10) — add CI guardrails registry COMPLETENESS LOCK gate, **narrow `CI_Guardrails_Index_v1.0.md` from 219 lines to a pure registry-only surface (-270/+1 lines)**.
>
> The index file's canonical shape at HEAD is a single `SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN`/`_END` block containing ~57 gate entries. **No title, no prose, no contents, no TOC.** Adding the deleted marker families back would mean inserting prose content into an index that was deliberately stripped — direct conflict with Phase 7.8 design.

This forecloses Interpretation 1. Phase 7.8 made the index *narrower*, not wider, by deliberate design. Adding new categories (invariant docs, proof runners) to the index would directly conflict with that design and would also trigger the surface-freeze gate's fingerprint check, requiring rebase.

### The 2026-04-27 retirement precedent

From `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md`:

> Commit `0faf0c0` (Phase 7.8, 2026-03-10) deleted 270 lines of prose from `CI_Guardrails_Index_v1.0.md`, removing 43 SV markers in the process. **Five gates were left silently failing — checking for markers and bullets that no longer existed.**
>
> Three gates retired wholesale:
> - `gate_ci_proof_surface_registry_index_discoverability_v1.sh` (Finding C — pure marker+bullet check, no other logic)
> - `gate_creative_surface_registry_discoverability_v1.sh` (Finding E — pure marker+bullet check, no other logic)
> - **`gate_docs_integrity_v2.sh` (Finding F — discovered this session; pure marker check only)**
>
> Two gates surgically edited (real non-marker logic preserved): `gate_creative_surface_registry_usage_v1.sh` and `gate_docs_mutation_guardrail_v2.sh`.

The precedent for handling Phase 7.8 dormancy residue is established and was commissioner-authorized at the time. **A `gate_docs_integrity_v2.sh` was retired specifically as part of this cluster.** Today's failure is from a *different* gate — `scripts/check_docs_integrity_v1.py`, the `v1` version, written in Python — that survived the 2026-04-27 retirement pass because it was not a shell gate doing pure marker checks. But its `gate_ci_index_coverage` function exhibits the same dormancy pattern.

### The 2026-04-28 standing-items finding

From `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`'s `prove_ci.sh` standing-items baseline:

> The standing items remain: `_status.sh` missing, 6× memory_events allowlist violations, **Docs integrity gate self-referential coverage gap**, 3× Voice variant rendering retired, `gate_contract_linkage_v1.sh` missing, `pfl.registry` ModuleNotFoundError.

Track A's commit message body explicitly named "Docs integrity gate self-referential coverage gap" as a known standing item on 2026-04-28 — five days before today, the day before H1+H4's errexit (commit `bfee780`, 2026-04-29) made it visible. The gap was already known; H1+H4 just surfaced it.

## What the gate's other functions do

Reading `scripts/check_docs_integrity_v1.py` end-to-end establishes that `gate_ci_index_coverage` is the only dormant check. The other three gates in the file are doing real, currently-relevant work:

- **`gate_header_presence`** — enforces that versioned canonical artifacts in `docs/canonical/` contain `[SV_CANONICAL_HEADER_V1]`. Scope explicitly narrowed by `docs_integrity_scope_canonical_only_v1`. Live validation surface.
- **`gate_duplicate_basenames`** — detects two canonical-looking artifacts with the same filename. Real refactor-time guard.
- **`extract_doc_map_refs` + `gate_doc_map_refs_exist`** — reads `DOC_MAPS_V1` (verified to point at extant files: `docs/canonical/Documentation_Map_and_Canonical_References.md` and `docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md`), extracts referenced paths, validates each `docs/` or `scripts/` path exists. Currently functional.

Wholesale retirement of `check_docs_integrity_v1.py` would lose this validation work. **The file deserves preservation; only the dormant invocation needs removing.**

## Position 3 selected

Interpretation 3 (stale-assumption gate) plus Position-3-style surgical retirement is the architecturally correct resolution. The reasoning chain in canonical-document order:

1. Phase 7.8 (`0faf0c0`, 2026-03-10) deliberately narrowed `CI_Guardrails_Index_v1.0.md` to a pure-registry-only surface, removing prose content that previously included references to invariant docs and proof runners.
2. `gate_ci_index_coverage` was written against the pre-Phase-7.8 index shape. After Phase 7.8, the gate's literal substring checks targeted content that no longer existed in the file by design.
3. The 2026-04-27 retirement pass identified five gates with this exact pattern of Phase-7.8-induced dormancy. Three were retired wholesale; two were surgically edited to preserve real logic. `gate_docs_integrity_v2.sh` was retired wholesale as part of that pass.
4. `check_docs_integrity_v1.py`'s `gate_ci_index_coverage` is a sixth instance of the same Phase-7.8 dormancy pattern, missed by the 2026-04-27 pass because the v1 file is Python (not a shell gate) and contains real-work functions alongside the dormant one.
5. The surgical edit (parallel to the 2026-04-27 surgical edits to `gate_creative_surface_registry_usage_v1.sh` and `gate_docs_mutation_guardrail_v2.sh`) preserves the file's three real-work gates while removing the dormant invocation. The other gates' validation surface is preserved; the Phase 7.8 dormancy residue is closed.

The 2026-04-27 commissioner authorization for Path A retirement of Phase 7.8 dormancy residue establishes precedent. This resolution applies the same precedent to a sixth instance of the same root cause.

## Why Interpretation 1 was rejected

Interpretation 1 (expand the index's scope to include invariant docs and proof runners) was rejected because it would directly conflict with Phase 7.8's deliberate scope reduction.

The Phase 7.8 commit (`0faf0c0`) named "CI Guardrail Registry Completeness Lock" explicitly added a Registry Completeness gate while wholesale removing the prose-rich Index. The index's narrow scope is not an accident; it is the architectural shape Phase 7.8 established. Re-expanding it would:

- Conflict with the index file's own framing (`# CI Guardrails Ops Entrypoints` header asserts gate-scripts-only scope).
- Trigger the surface-freeze gate's fingerprint check, requiring fingerprint rebase as a separate concern.
- Reintroduce the prose maintenance burden Phase 7.8 was specifically designed to eliminate.

Interpretation 1 essentially proposes undoing Phase 7.8 to satisfy a gate written against the pre-Phase-7.8 shape. The architecturally correct direction is the opposite: update the gate to match Phase 7.8, not undo Phase 7.8 to match the gate.

## Why Interpretation 2 was rejected

Interpretation 2 (redirect the gate to a different index file) was rejected because the gate's check is fundamentally about prose content that no longer exists *anywhere by design*.

A redirect would require finding an alternative index file that does include prose references to `Docs_Integrity_Gate_Invariant_v1.0.md` and `prove_docs_integrity_v1.sh`. `CI_Proof_Surface_Registry_v1.0.md` does reference the proof runner (lines 11, 63), so it could plausibly be the redirect target — but Phase 7.8's design philosophy was to eliminate prose-reference indexes specifically because of their maintenance burden. Adding the gate's check to a different index would propagate the same dormancy risk to that other index when it inevitably gets restructured later.

The cleaner answer is: the gate's check is itself the dormancy. Removing the check rather than redirecting it aligns with Phase 7.8's intent and matches the 2026-04-27 retirement precedent.

## Surgical edit scope (for the follow-on session)

The follow-on refactor session should make the following edits to `scripts/check_docs_integrity_v1.py`:

1. Remove the function definition `gate_ci_index_coverage(ci_index: Path)` (currently at lines 126-138).
2. In `main()` (currently around lines 158-161):
   - Remove the `ci_index = REPO_ROOT / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"` assignment.
   - Remove the existence check (`if not ci_index.exists(): die(...)`).
   - Remove the `gate_ci_index_coverage(ci_index)` call.
3. Verify no other callers of `gate_ci_index_coverage` exist (a `grep -n "gate_ci_index_coverage"` should return only the now-removed lines).

After the surgical edit, `prove_ci.sh` should pass cleanly through `check_docs_integrity_v1.py` (the remaining three gates are healthy at HEAD per the doc-read). Whether `prove_ci.sh` returns rc=0 overall depends on whether any further-downstream gates have additional dormancy residue this session did not surface.

## Side-findings worth recording for separate sessions

The doc-read also surfaced two minor side-findings about `check_docs_integrity_v1.py` that are not in this resolution's scope but should be tracked:

**Side-finding A — `extract_doc_map_refs` may surface false positives.** The function uses both a markdown-link regex (`MD_LINK_RE`) *and* a generic path-token regex (`PATH_TOKEN_RE`) to extract referenced paths. The path-token regex matches any `docs/...` or `scripts/...` substring in prose, not just intentional references. If `DOC_MAPS_V1` files contain prose mentioning paths that no longer exist (e.g., archived patches, retired gates), `gate_doc_map_refs_exist` could fail spuriously. Worth a separate audit session to confirm the doc maps are clean.

**Side-finding B — `DOC_MAPS_V1` is hardcoded.** The constant lists exactly two files. If new doc maps are added to the project, they would not be checked by `gate_doc_map_refs_exist` unless the constant is updated. Not a current bug (the two paths exist), but a maintenance surface worth noting.

Neither side-finding blocks this resolution or the follow-on refactor. They are recorded here so future-Steve has them in scope.

## What this memo does not do

- **Does not execute the surgical edit.** Per session discipline established in today's H7 Cat B sequence (escalation → resolution → refactor), one topic per session. This session resolves the architectural question; the next session executes the code change.
- **Does not amend Phase 7.8 or its descendant memos.** Phase 7.8's design is correct. The 2026-04-27 retirement memo's reasoning extends naturally to this case; no amendment is needed.
- **Does not propose retiring `check_docs_integrity_v1.py` wholesale.** The file's three real-work gates (header presence, duplicate basenames, doc map refs) are functional and worth preserving. Surgical edit is the right scope.
- **Does not close the side-findings.** Side-findings A and B are recorded for separate sessions, not resolved here.

## Cross-references

- `_observations/OBSERVATIONS_2026_05_02_DOCS_INTEGRITY_GATE_FINDING.md` (74f58c8) — the finding memo this resolution closes.
- `_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_RETIRED.md` — first retirement of Phase 7.8 dormancy residue; established the archaeology pattern.
- `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` — three additional retirements + two surgical edits in the same Phase 7.8 cluster. Most direct precedent for this resolution.
- `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — names "Docs integrity gate self-referential coverage gap" as a known standing item on 2026-04-28.
- Commit `0faf0c0` (2026-03-10) — Phase 7.8 — CI Guardrail Registry Completeness Lock. The root cause of the dormancy.
- Commit `a6657b1` — "Docs: add canonical docs integrity gate (v1)". The gate's establishing commit. Predates Phase 7.8 (date not verified in this memo; the Phase 7.8 root cause holds regardless of `a6657b1`'s exact date).
- Commit `bfee780` (2026-04-29) — H1+H4 closure adding `set -euo pipefail` to `prove_ci.sh`, which made silently-failing dormant gates visible.
- `_observations/OBSERVATIONS_2026_05_02_H7_CAT_B_RESOLUTION.md` — today's H7 Cat B resolution memo. This resolution follows the same shape.

## Append-only

This memo records the resolution. It does not edit any prior memo, the gate, the index, or `prove_ci.sh`. The gate continues to fail at rc=1; the failure is now an explicitly-recorded transitional condition with a known and well-precedented resolution path, awaiting execution in a follow-on session.
