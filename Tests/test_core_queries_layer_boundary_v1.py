"""Layer-boundary gate for core/queries/.

Query helpers must read from canonical payload fields only. Parsing
adapter-specific raw payloads (e.g. MFL's ``raw_mfl_json``) belongs in
``ingest/`` — the canonical layer should expose structured data and
queries should consume it.

This gate is scoped to ``src/squadvault/core/queries/`` specifically
(not all of ``core/``) because other ``core/`` subsystems have
defensible reasons to touch raw payloads (notably
``core/canonicalize/``, whose entire purpose is raw-to-canonical
derivation). Those are distinct concerns documented in
``_observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md``.

This test resolves the query-layer aspect of Audit Surprise S10.
"""
from __future__ import annotations

from pathlib import Path

QUERIES_DIR = (
    Path(__file__).resolve().parent.parent
    / "src" / "squadvault" / "core" / "queries"
)


def test_core_queries_contains_no_raw_mfl_json_reference():
    """No file under core/queries/ may reference the adapter-specific payload field.

    If this test fails, a query helper is once again reaching into
    raw_mfl_json — meaning the canonical payload does not expose what
    the helper needs, and the fix is to promote the required structure
    into the canonical payload at ingest time, not to parse raw here.
    """
    assert QUERIES_DIR.is_dir(), f"expected queries dir at {QUERIES_DIR}"

    offenders: list[str] = []
    for py_file in sorted(QUERIES_DIR.rglob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        if "raw_mfl_json" in text:
            offenders.append(str(py_file.relative_to(QUERIES_DIR.parents[3])))

    assert not offenders, (
        "core/queries/ must not reference raw_mfl_json. Offenders:\n  "
        + "\n  ".join(offenders)
        + "\nPromote the required structure into the canonical payload "
        "at ingest time instead."
    )
