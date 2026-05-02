"""Tests for the reception capture sibling files (operational, not Platform).

Reception observations are written to sibling YAML files next to each
archive entry:

    archive/recaps/<season>/week_<NN>__v<V>__reception.yaml

These tests are vacuous when no reception files exist. As reception
data accumulates, they enforce:

- Filename pattern: ``week_NN__vV__reception.yaml``.
- Pairing: every reception file has a matching archive ``.md``.
- Document stream: each YAML document parses (focused parser, matching
  the distribution archive layout test convention; no PyYAML dep).
- Required keys per document.
- ``observation_id`` values are 1..N monotonic within a file.
- ``kind`` is one of the closed enum.
- ``silence_period_close`` is terminal (at most one per file, and last
  if present).
- ``observed_at`` parses as ISO-8601 UTC with microsecond precision.

The append-only invariant cannot be verified from filesystem state;
that is enforced at write time inside ``scripts/record_reception.py``.

Captured observations are facts. These tests check structural drift,
not content quality. The Platform Guardrails forbid scoring or
aggregating observations into engagement metrics; that constraint
lives in the runbook and the script's design, not in tests.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_RECAPS = REPO_ROOT / "archive" / "recaps"

_RECEPTION_FILENAME_RE = re.compile(
    r"^week_(\d{2})__v(\d+)__reception\.yaml$"
)
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,6}Z$"
)

_REQUIRED_DOC_KEYS = (
    "observation_id",
    "observed_at",
    "observed_by",
    "kind",
    "member",
    "content",
    "context",
    "notes",
)

_ALLOWED_KINDS = {
    "reply",
    "reaction",
    "reference",
    "silence_period_close",
}
_TERMINAL_KIND = "silence_period_close"


def _iter_reception_files() -> list[Path]:
    if not ARCHIVE_RECAPS.exists():
        return []
    return sorted(ARCHIVE_RECAPS.glob("*/week_*__v*__reception.yaml"))


def _split_documents(text: str) -> list[str]:
    """Split a YAML stream on ``---`` separators.

    The emitter writes each document as ``---\\n<body>\\n``. Splitting
    on the leading ``---\\n`` and discarding the empty pre-block yields
    one chunk per document. Documents do not themselves contain a
    line equal to ``---`` (only as the leading separator), so this
    split is unambiguous for the emitter's output.
    """
    chunks = text.split("---\n")
    return [chunk for chunk in chunks if chunk.strip()]


def _parse_document(chunk: str) -> dict[str, str]:
    """Parse one YAML document into a top-level key→raw-value map.

    Handles two value shapes the emitter produces:
    - Scalar lines: ``key: value``.
    - Block literals: ``key: |`` followed by indented lines.

    Block-literal continuation lines are joined into ``\\n``-separated
    text. Only top-level keys are surfaced; this is enough to assert
    structural and enum constraints. The field set is closed and the
    emitter is the only writer, so a hand-written parser is sufficient
    and avoids pulling in PyYAML.
    """
    out: dict[str, str] = {}
    lines = chunk.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith(" "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "|":
            block_lines: list[str] = []
            i += 1
            while i < len(lines) and (
                lines[i].startswith("  ") or lines[i] == ""
            ):
                block_lines.append(lines[i][2:] if lines[i].startswith("  ") else "")
                i += 1
            out[key] = "\n".join(block_lines)
            continue
        out[key] = value
        i += 1
    return out


def _strip_quotes(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return raw


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reception_files_match_naming_pattern() -> None:
    """Every reception file matches the contracted filename pattern."""
    for path in _iter_reception_files():
        assert _RECEPTION_FILENAME_RE.match(path.name), (
            f"unexpected reception filename: {path}"
        )


def test_reception_files_pair_with_archive_md() -> None:
    """Every reception file has a matching archive .md (no orphans)."""
    for path in _iter_reception_files():
        match = _RECEPTION_FILENAME_RE.match(path.name)
        assert match is not None
        week = match.group(1)
        version = match.group(2)
        md_path = path.parent / f"week_{week}__v{version}.md"
        assert md_path.exists(), (
            f"reception file {path} has no matching archive .md at {md_path}"
        )


def test_reception_documents_have_required_keys() -> None:
    """Each YAML document carries the contracted top-level keys."""
    for path in _iter_reception_files():
        text = path.read_text(encoding="utf-8")
        docs = _split_documents(text)
        assert docs, f"reception file {path} contains no documents"
        for idx, chunk in enumerate(docs, start=1):
            doc = _parse_document(chunk)
            for key in _REQUIRED_DOC_KEYS:
                assert key in doc, (
                    f"{path} doc#{idx}: missing required key '{key}'"
                )


def test_reception_observation_ids_monotonic() -> None:
    """Within a file, observation_id values are 1..N monotonic."""
    for path in _iter_reception_files():
        text = path.read_text(encoding="utf-8")
        docs = _split_documents(text)
        ids: list[int] = []
        for idx, chunk in enumerate(docs, start=1):
            doc = _parse_document(chunk)
            raw = doc["observation_id"]
            try:
                ids.append(int(raw))
            except ValueError:
                raise AssertionError(
                    f"{path} doc#{idx}: observation_id is not an integer: {raw!r}"
                ) from None
        for expected, actual in enumerate(ids, start=1):
            assert expected == actual, (
                f"{path}: observation_id sequence broken at position "
                f"{expected}: got {actual}"
            )


def test_reception_kind_in_allowed_enum() -> None:
    """Each document's ``kind`` is one of the closed enum."""
    for path in _iter_reception_files():
        text = path.read_text(encoding="utf-8")
        docs = _split_documents(text)
        for idx, chunk in enumerate(docs, start=1):
            doc = _parse_document(chunk)
            kind = _strip_quotes(doc["kind"])
            assert kind in _ALLOWED_KINDS, (
                f"{path} doc#{idx}: kind '{kind}' not in {sorted(_ALLOWED_KINDS)}"
            )


def test_reception_silence_close_is_terminal_and_unique() -> None:
    """``silence_period_close`` appears at most once and is last if present."""
    for path in _iter_reception_files():
        text = path.read_text(encoding="utf-8")
        docs = _split_documents(text)
        kinds = [_strip_quotes(_parse_document(d)["kind"]) for d in docs]
        terminal_positions = [
            i for i, k in enumerate(kinds) if k == _TERMINAL_KIND
        ]
        assert len(terminal_positions) <= 1, (
            f"{path}: more than one silence_period_close recorded "
            f"(positions {terminal_positions})"
        )
        if terminal_positions:
            assert terminal_positions[0] == len(kinds) - 1, (
                f"{path}: silence_period_close is not the last document "
                f"(found at position {terminal_positions[0]} of {len(kinds) - 1})"
            )


def test_reception_observed_at_is_iso8601_utc() -> None:
    """Each ``observed_at`` parses as ISO-8601 UTC with microseconds."""
    for path in _iter_reception_files():
        text = path.read_text(encoding="utf-8")
        docs = _split_documents(text)
        for idx, chunk in enumerate(docs, start=1):
            doc = _parse_document(chunk)
            raw = _strip_quotes(doc["observed_at"])
            assert _TIMESTAMP_RE.match(raw), (
                f"{path} doc#{idx}: observed_at not ISO-8601 UTC microseconds: {raw!r}"
            )
            # Round-trip parse to be extra strict on real validity.
            try:
                datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError as exc:
                raise AssertionError(
                    f"{path} doc#{idx}: observed_at unparseable: {raw!r} ({exc})"
                ) from None


# ---------------------------------------------------------------------------
# Emitter unit tests (exercise the script's render against the test parser)
# ---------------------------------------------------------------------------

import sys  # noqa: E402

_SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))
import record_reception  # noqa: E402


def _render(**overrides: object) -> str:
    """Render one document with sensible defaults for tests."""
    base: dict[str, object] = {
        "observation_id": 1,
        "observed_at": "2026-04-29T03:14:00.000000Z",
        "observed_by": "weichert",
        "kind": "reply",
        "member": "miller",
        "content": "haha brutal on the bench points line",
        "context": "group_text_thread",
        "notes": None,
    }
    base.update(overrides)
    doc = record_reception.ReceptionDoc(**base)  # type: ignore[arg-type]
    return record_reception._render_document(doc)


def test_emitter_output_parses_through_test_parser() -> None:
    """The emitter's output round-trips through the layout parser cleanly."""
    rendered = _render()
    chunks = _split_documents(rendered)
    assert len(chunks) == 1
    parsed = _parse_document(chunks[0])
    for key in _REQUIRED_DOC_KEYS:
        assert key in parsed, f"emitted doc missing key {key!r}"
    assert _strip_quotes(parsed["kind"]) == "reply"
    assert _strip_quotes(parsed["member"]) == "miller"
    assert int(parsed["observation_id"]) == 1


def test_emitter_handles_null_member_and_content() -> None:
    """For silence_period_close, member and content are null."""
    rendered = _render(
        kind="silence_period_close", member=None, content=None,
        context="7_day_window_close",
    )
    parsed = _parse_document(_split_documents(rendered)[0])
    assert parsed["member"] == "null"
    assert parsed["content"] == "null"


def test_emitter_block_literal_for_multiline_notes() -> None:
    """Multi-line notes render as a YAML block literal that round-trips."""
    rendered = _render(notes="line one\nline two\nline three")
    parsed = _parse_document(_split_documents(rendered)[0])
    assert parsed["notes"] == "line one\nline two\nline three"


def test_emitter_quotes_escape_correctly() -> None:
    """Embedded quotes and backslashes survive the round trip."""
    tricky = 'said "hello" with a \\ backslash'
    rendered = _render(content=tricky)
    parsed = _parse_document(_split_documents(rendered)[0])
    assert _strip_quotes(parsed["content"]) == tricky


def test_next_observation_id_on_missing_file(tmp_path: Path) -> None:
    """First observation in a fresh file is id 1."""
    missing = tmp_path / "week_07__v27__reception.yaml"
    assert record_reception._next_observation_id(missing) == 1


def test_next_observation_id_increments(tmp_path: Path) -> None:
    """Subsequent observations get max+1."""
    path = tmp_path / "week_07__v27__reception.yaml"
    path.write_text(_render(observation_id=1) + _render(observation_id=2),
                    encoding="utf-8")
    assert record_reception._next_observation_id(path) == 3


def test_terminal_observation_detected(tmp_path: Path) -> None:
    """Presence of silence_period_close is detected for refusal logic."""
    path = tmp_path / "week_07__v27__reception.yaml"
    path.write_text("", encoding="utf-8")
    assert record_reception._has_terminal_observation(path) is False
    path.write_text(
        _render(observation_id=1, kind="silence_period_close",
                member=None, content=None, context="7_day_window_close",
                notes="Window closed silent."),
        encoding="utf-8",
    )
    assert record_reception._has_terminal_observation(path) is True
