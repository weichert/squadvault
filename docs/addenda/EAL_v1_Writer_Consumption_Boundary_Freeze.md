# Editorial Attunement Layer (EAL) v1 — Writer Consumption Boundary (Frozen)

Status: **FROZEN**  
Tag: **eal-v1-writer-boundary**  
Date: 2026-01-26

## What is frozen

EAL v1 is complete across:

- Directive computation (existing)
- Persistence (existing; additive metadata)
- Schema + trace contract (existing)
- **Writer consumption boundary (v1)** — read-only, explicit, single wiring point
- Guardrail test proving invariants

## Hard constraints (non-negotiable)

EAL v1 **must not** modify:

- selection
- ordering
- canonical facts
- window bounds

EAL v1 **may only** constrain expression downstream (future work), and remains metadata-only at render.

## Deterministic wiring point

Creative/draft lifecycle loads directives **read-only** immediately before rendering:

- `src/squadvault/recaps/weekly_recap_lifecycle.py`  
  loads `load_eal_directives_v1(...)` and passes `eal_directives` into the renderer

Renderer accepts `eal_directives` but does not apply creative logic:

- `src/squadvault/core/recaps/render/render_recap_text_v1.py`  
  `_ = eal_directives` (accepted, ignored)

## Guardrail

Test ensures EAL cannot affect selection/window invariants:

- `Tests/test_eal_writer_boundary_v1.py`

This test is authoritative: if it fails, the boundary has been violated.

## Notes on optional persistence

The EAL consumer treats a missing persistence table as neutral (returns `None`),
preserving compatibility with DBs that do not yet include the EAL directives table.
