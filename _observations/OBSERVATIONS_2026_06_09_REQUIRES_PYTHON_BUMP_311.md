# Observations - requires-python bumped to >=3.11

**Date:** 2026-06-09
**Session:** Follow-up to charter adoption / E1.1 - resolve the requires-python hazard.
**HEAD at authoring:** `e6da7d6`

---

## What shipped

- `pyproject.toml`: `requires-python` `">=3.10"` -> `">=3.11"`. The codebase already
  requires 3.11+ (`prompt_audit_v1.py` uses `from datetime import UTC`), so the old
  floor understated the true requirement. CI already runs 3.12; no ci.yml change needed.

## Finding: the bump retargets ruff (verify-first catch)

Ruff infers `target-version` from `requires-python`. Moving the floor to 3.11 retargeted
ruff to py311 and surfaced 38 errors that the py310 target had suppressed:

- **UP017 (21, safe autofix):** "Use `datetime.UTC` alias." Applied via `ruff --fix`.
  `timezone.utc` and `datetime.UTC` are the *same singleton object*
  (`datetime.UTC is timezone.utc` -> True), so output is byte-identical and the
  determinism / golden-path gates are unaffected. The fix also harmonized the codebase,
  which already used `datetime.UTC` in `prompt_audit_v1.py`. Cascaded into I001/F401
  import cleanups; 16 files touched.
- **UP042 (21, NOT applied):** "str+Enum -> StrEnum." Behavior-sensitive: for
  `class X(str, Enum)`, `str(X.A)` yields `"X.A"`; for `StrEnum` it yields the value
  `"a"`. These enums (VerdictStatus, MissingWeeksPolicy, FormalityLevel, ...) are
  contract/serialization-bearing, so migrating risks changing recap output and tripping
  determinism gates. **Deferred** behind a targeted `UP042` ignore in `pyproject.toml`
  with rationale, per founder decision. Registered as an open item in STATE.md.

## Decision (founder)

Offered three scopings (minimal/decouple, fix-all-now, bump + UP017 + defer UP042).
Founder chose **bump + UP017 fix + defer UP042**. The StrEnum migration becomes its own
risk-managed unit with determinism + golden-path validation before the ignore is dropped.

## Validation

- `ruff check src/squadvault/` -> zero (UP042 ignored).
- mypy: 158 files clean (under 3.11).
- Full suite: 2358 passed, 2 skipped (under 3.11).
- prove_ci: run under the 3.11 PATH shim per the standing local-interpreter hazard.

## Lesson

`requires-python` is not inert metadata in this repo - it is ruff's lint-target source.
Any future floor change should be expected to move the lint surface; budget for the
ripple rather than treating the bump as a one-liner.
