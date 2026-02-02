# SquadVault

**SquadVault is a deterministic recap engine with governed expressive output.**

It produces auditable, fact-locked weekly recaps from event data, while allowing explicitly non-canonical narrative and voice variants to be generated downstream — safely, repeatably, and without contaminating the source of truth.

SquadVault is built for group systems where shared history matters more than real-time optimization.

---

## What Problem Does SquadVault Solve?

Most recap or summary systems collapse three concerns into one:

- data truth
- narrative interpretation
- stylistic expression

That collapse makes systems brittle:
- facts drift
- summaries change silently
- creative output becomes untraceable

**SquadVault separates these concerns by design.**

- Canonical facts are deterministic, immutable, and auditable
- Editorial review is explicit and lifecycle-governed
- Expressive output is downstream, non-canonical, and clearly labeled

The result is a system where facts never change accidentally, creativity is allowed but constrained, and every output can be traced back to an approved source.

---

## Core Principles

- **Facts first, always**  
  Canonical artifacts are deterministic and immutable once approved.

- **Explicit separation of truth and expression**  
  Narrative, tone, and voice never write back to canonical storage.

- **No hidden inference**  
  The system does not guess, infer, or fabricate missing details.

- **Lifecycle over convenience**  
  Every recap moves through explicit states: drafted → reviewed → approved or withheld.

- **Auditability is a feature**  
  Fingerprints, counts, and traceability are preserved end-to-end.

---

## High-Level Workflow

1. Ingest and canonicalize events
2. Select events for a weekly window
3. Generate a deterministic recap draft
4. Human editorial review
5. Approve or withhold the recap
6. Export outputs
   - canonical recap (facts only)
   - non-canonical voice variants
   - non-canonical narrative assemblies

Once approved, the canonical recap cannot change. All expressive output is strictly downstream.

---

## Canonical vs Non-Canonical Outputs

**Canonical (immutable once approved):**

- weekly recap artifacts
- fact blocks
- event counts
- selection fingerprints
- traceability metadata

**Non-Canonical (export-only, derived from approved artifacts):**

- voice variants (e.g., neutral, playful, dry)
- narrative assemblies and sharepacks

---

## Quick Start (Operator)

Run a non-destructive weekly gate:

./scripts/recap check \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2025 \
  --week-index 1 \
  --approved-by steve

Render an approved recap (facts-only view):

./scripts/recap render-week \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2025 \
  --week-index 1 \
  --approved-only

Export non-canonical deliverables (approved artifacts only):

./scripts/recap export-approved \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2025 \
  --week-index 1 \
  --export-dir artifacts

Export deterministic narrative assemblies (approved-only):

./scripts/recap export-assemblies \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2025 \
  --week-index 1 \
  --export-dir artifacts

---

## Export Locations

Exports are written under:

artifacts/exports/<league_id>/<season>/week_<NN>/

Examples:

variants_pack_vXX.md
assembly_plain_v1__approved_vXX.md
assembly_sharepack_v1__approved_vXX.md

All exported files are explicitly labeled NON-CANONICAL.

---

## Operator Documentation

Weekly recap commands and golden path: docs/operator-weekly-recap.md

Ingestion and historical setup notes: docs/ingestion-mfl-notion.md

---

## Status

The Creative Layer is complete and locked:

Voice Variant Export (Phase 2.2)

Deterministic Narrative Assembly (Phase 2.3)

---

