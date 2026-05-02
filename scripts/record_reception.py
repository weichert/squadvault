#!/usr/bin/env python3
"""Record one reception observation against an archived distribution.

Track B operational tooling. Reception observations are facts about how
the league related to a distributed recap — replies, reactions,
unprompted references, or the close of a silence window. They are not
metrics, not engagement signal, and not aggregable.

Each observation is appended as a YAML document to a sibling file next
to the archive entry it observes:

    archive/recaps/<season>/week_<NN>__v<V>__reception.yaml

The original distribution ``.md`` and ``.json`` are never touched after
creation; reception is a separate accreting log. Append-only at the
file level: new documents append to the end, prior documents are never
rewritten.

Captured observations serve voice quality (does the content feel like
the league?), not engagement (does the league engage more?). The
distinction is binding per the Platform Guardrails.

Exit codes
----------
0   success
2   archive entry not found for the requested (season, week, version)
3   invalid combination of arguments (e.g., kind without content)
4   silence_period_close already recorded for this artifact
5   commissioner declined the confirmation prompt
"""
from __future__ import annotations

import argparse
import getpass
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

DEFAULT_ARCHIVE_ROOT: Final[str] = "archive/recaps"
DEFAULT_CONTEXT: Final[str] = "group_text_thread"
SILENCE_CONTEXT: Final[str] = "7_day_window_close"

ALLOWED_KINDS: Final[frozenset[str]] = frozenset(
    {"reply", "reaction", "reference", "silence_period_close"}
)
TERMINAL_KIND: Final[str] = "silence_period_close"

# Document key order is part of the contract. Reading sibling files
# top-to-bottom should always show identity first, observed event next,
# detail and notes last.
_DOC_KEY_ORDER: Final[tuple[str, ...]] = (
    "observation_id",
    "observed_at",
    "observed_by",
    "kind",
    "member",
    "content",
    "context",
    "notes",
)


@dataclass(frozen=True)
class ReceptionDoc:
    """One reception observation as it will be written."""

    observation_id: int
    observed_at: str
    observed_by: str
    kind: str
    member: str | None
    content: str | None
    context: str
    notes: str | None


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _archive_md_path(
    archive_root: Path, *, season: int, week_index: int, version: int
) -> Path:
    return archive_root / str(season) / f"week_{week_index:02d}__v{version}.md"


def _reception_path(
    archive_root: Path, *, season: int, week_index: int, version: int
) -> Path:
    return (
        archive_root
        / str(season)
        / f"week_{week_index:02d}__v{version}__reception.yaml"
    )


# ---------------------------------------------------------------------------
# Reading the existing log (for next id and terminal-kind check)
# ---------------------------------------------------------------------------


_OBS_ID_RE = re.compile(r"^observation_id:\s*(\d+)\s*$", re.MULTILINE)
_KIND_RE = re.compile(r'^kind:\s*"?([a-z_]+)"?\s*$', re.MULTILINE)


def _next_observation_id(reception_path: Path) -> int:
    """Compute the next observation_id by scanning the existing file.

    Reads top-level ``observation_id:`` lines (block-literal indented
    lines never have this key by construction). Returns 1 when the
    file does not exist or contains no observations.
    """
    if not reception_path.exists():
        return 1
    text = reception_path.read_text(encoding="utf-8")
    ids = [int(m.group(1)) for m in _OBS_ID_RE.finditer(text)]
    return max(ids) + 1 if ids else 1


def _has_terminal_observation(reception_path: Path) -> bool:
    """Return True when the file already contains a silence_period_close.

    The terminal kind is allowed at most once per artifact: it records
    the close of the 7-day reception window and there is no second
    close.
    """
    if not reception_path.exists():
        return False
    text = reception_path.read_text(encoding="utf-8")
    return any(m.group(1) == TERMINAL_KIND for m in _KIND_RE.finditer(text))


def _count_prior_observations(reception_path: Path) -> int:
    """Return the count of observations recorded so far.

    Used only to compose the default notes for a silence_period_close.
    Carries no operational meaning beyond message construction.
    """
    if not reception_path.exists():
        return 0
    text = reception_path.read_text(encoding="utf-8")
    return sum(1 for _ in _OBS_ID_RE.finditer(text))


# ---------------------------------------------------------------------------
# YAML emission (focused, no library dependency)
# ---------------------------------------------------------------------------


def _yaml_scalar(value: object) -> str:
    """Emit one scalar matching the distribute script's convention.

    Strings are double-quoted with backslashes and double-quotes
    escaped. Integers emit bare. ``None`` becomes ``null``.
    Multi-line strings are not handled here — see ``_emit_pair`` for
    the block-literal path.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _emit_pair(key: str, value: object) -> list[str]:
    """Emit one ``key: value`` pair, choosing scalar vs block-literal.

    A string with embedded newlines becomes a YAML block literal:

        notes: |
          line one
          line two

    Anything else becomes a scalar on one line.
    """
    if isinstance(value, str) and "\n" in value:
        body = value.rstrip("\n")
        indented = "\n".join(f"  {line}" if line else "" for line in body.split("\n"))
        return [f"{key}: |", indented]
    return [f"{key}: {_yaml_scalar(value)}"]


def _render_document(doc: ReceptionDoc) -> str:
    """Render one observation as a YAML document.

    The leading ``---`` makes the file ``yaml.safe_load_all``-parseable
    as a stream. Trailing newline follows the block.
    """
    fields: dict[str, object] = {
        "observation_id": doc.observation_id,
        "observed_at": doc.observed_at,
        "observed_by": doc.observed_by,
        "kind": doc.kind,
        "member": doc.member,
        "content": doc.content,
        "context": doc.context,
        "notes": doc.notes,
    }
    lines: list[str] = ["---"]
    for key in _DOC_KEY_ORDER:
        lines.extend(_emit_pair(key, fields[key]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Append (the only write semantic)
# ---------------------------------------------------------------------------


def _append_document(reception_path: Path, doc_text: str) -> None:
    """Append one rendered document to the reception file.

    Creates the file if missing. The parent directory is the archive
    season directory, which already exists by the time any reception
    can be recorded (the archive .md is the precondition).
    """
    reception_path.parent.mkdir(parents=True, exist_ok=True)
    with reception_path.open("a", encoding="utf-8") as fh:
        fh.write(doc_text)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """ISO-8601 UTC timestamp matching the distribute script's format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---------------------------------------------------------------------------
# Argument parsing and validation
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record one reception observation against an archived "
            "distribution. Append-only; sibling YAML log next to the "
            "archive .md."
        ),
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week-index", type=int, required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument(
        "--archive-root",
        default=DEFAULT_ARCHIVE_ROOT,
        help="Root directory of the distribution archive.",
    )
    parser.add_argument(
        "--observed-by",
        default=None,
        help="Observer label (default: current user).",
    )
    parser.add_argument(
        "--observed-at",
        default=None,
        help="ISO-8601 UTC timestamp (default: now).",
    )
    parser.add_argument(
        "--kind",
        choices=sorted(ALLOWED_KINDS),
        help="Observation kind. Required unless --silence-window-close.",
    )
    parser.add_argument(
        "--member",
        default=None,
        help="Member shorthand (franchise short or owner first name).",
    )
    parser.add_argument(
        "--content",
        default=None,
        help="Single-line observation content. See --content-stdin for paste.",
    )
    parser.add_argument(
        "--content-stdin",
        action="store_true",
        help="Read content from stdin (multi-line supported).",
    )
    parser.add_argument(
        "--context",
        default=DEFAULT_CONTEXT,
        help=f"Where the observation came from (default: {DEFAULT_CONTEXT}).",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="Optional commissioner note.",
    )
    parser.add_argument(
        "--silence-window-close",
        action="store_true",
        help=(
            "Shorthand for --kind silence_period_close. Records the close "
            "of the 7-day reception window. Allowed at most once per "
            "artifact."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt before writing.",
    )
    return parser


class _BadArgs(Exception):
    """Raised when CLI argument validation fails. Mapped to exit code 3."""


def _resolve_kind(args: argparse.Namespace) -> str:
    if args.silence_window_close:
        if args.kind and args.kind != TERMINAL_KIND:
            raise _BadArgs(
                "Conflicting flags: --silence-window-close cannot be combined "
                f"with --kind {args.kind}."
            )
        return TERMINAL_KIND
    if not args.kind:
        raise _BadArgs(
            "Either --kind <kind> or --silence-window-close is required."
        )
    return str(args.kind)


def _resolve_content(args: argparse.Namespace, *, kind: str) -> str | None:
    if args.content_stdin and args.content is not None:
        raise _BadArgs("Use either --content or --content-stdin, not both.")
    if args.content_stdin:
        text = sys.stdin.read().rstrip("\n")
        return text or None
    if args.content is not None:
        return str(args.content)
    # silence_period_close legitimately has no content; reactions usually
    # do (the reaction name); replies and references must.
    if kind in {"reply", "reference"}:
        raise _BadArgs(
            f"--content is required for kind '{kind}'. Use --content-stdin "
            f"for multi-line input."
        )
    return None


# ---------------------------------------------------------------------------
# Confirmation and memo skeleton
# ---------------------------------------------------------------------------


def _confirm_interactive(doc: ReceptionDoc, reception_path: Path) -> bool:
    sys.stderr.write(
        "\nAbout to append this observation:\n"
        f"  file: {reception_path}\n"
        f"  observation_id: {doc.observation_id}\n"
        f"  kind: {doc.kind}\n"
        f"  member: {doc.member or '(none)'}\n"
        f"  content: {(doc.content or '')[:80] + ('...' if doc.content and len(doc.content) > 80 else '')}\n"
        "\nPress Enter to confirm, type 'no' to abort: "
    )
    sys.stderr.flush()
    return input().strip().lower() in ("", "y", "yes")


def _print_silence_memo_skeleton(
    *, season: int, week_index: int, version: int, prior_count: int
) -> None:
    """Emit a suggested observation memo path and skeleton on silence-close.

    Silence around a Writer's Room piece is a finding worth a memo per
    the runbook. The mechanism does not generate the memo — that is a
    commissioner reflection task — but printing the path and skeleton
    makes the next step trivially followable.
    """
    today = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    suggested = (
        f"_observations/OBSERVATIONS_{today}_S{season}_W{week_index:02d}_RECEPTION_WINDOW_CLOSE.md"
    )
    sys.stderr.write(
        "\nSilence-window-close recorded. Per the runbook, the close of\n"
        "a window with no/few observations is a finding worth a memo.\n"
        f"\nSuggested path:\n  {suggested}\n"
        "\nSuggested skeleton:\n"
        f"  # Reception window close — Season {season} Week {week_index} v{version}\n"
        "\n"
        "  ## Context\n"
        f"  Artifact: archive/recaps/{season}/week_{week_index:02d}__v{version}.md\n"
        f"  Observations recorded: {prior_count}\n"
        "\n"
        "  ## What was observed\n"
        "  [Summary of any reception observations during the window.]\n"
        "\n"
        "  ## What this tells us about voice / fit\n"
        "  [Commissioner reflection. Not a metric. Not an action item\n"
        "  unless the reflection produces one.]\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    archive_root = Path(args.archive_root).resolve()
    md_path = _archive_md_path(
        archive_root,
        season=args.season,
        week_index=args.week_index,
        version=args.version,
    )
    if not md_path.exists():
        sys.stderr.write(
            f"No archive entry found at {md_path}.\n"
            "Reception observations attach to a distributed artifact; "
            "distribute first via scripts/distribute_recap.py.\n"
        )
        return 2

    try:
        kind = _resolve_kind(args)
        content = _resolve_content(args, kind=kind)
    except _BadArgs as exc:
        sys.stderr.write(f"{exc}\n")
        return 3

    reception_path = _reception_path(
        archive_root,
        season=args.season,
        week_index=args.week_index,
        version=args.version,
    )

    if kind == TERMINAL_KIND and _has_terminal_observation(reception_path):
        sys.stderr.write(
            f"A silence_period_close is already recorded in {reception_path}.\n"
            "The terminal kind is allowed at most once per artifact.\n"
        )
        return 4

    observed_at = args.observed_at or _utc_now_iso()
    observed_by = args.observed_by or getpass.getuser()
    observation_id = _next_observation_id(reception_path)

    notes: str | None = args.notes
    if kind == TERMINAL_KIND and notes is None:
        prior = _count_prior_observations(reception_path)
        if prior == 0:
            notes = (
                "Window closed with no observations. Silence is a finding;\n"
                "logged here per the runbook."
            )
        else:
            notes = (
                f"Window closed after {prior} prior observation(s). No\n"
                "further reception observed in the window."
            )

    doc = ReceptionDoc(
        observation_id=observation_id,
        observed_at=observed_at,
        observed_by=observed_by,
        kind=kind,
        member=args.member,
        content=content,
        context=SILENCE_CONTEXT if kind == TERMINAL_KIND else args.context,
        notes=notes,
    )

    if not args.yes:
        try:
            confirmed = _confirm_interactive(doc, reception_path)
        except KeyboardInterrupt:
            sys.stderr.write("\nAborted: no observation written.\n")
            return 5
        if not confirmed:
            sys.stderr.write("Aborted: no observation written.\n")
            return 5

    _append_document(reception_path, _render_document(doc))

    sys.stderr.write(
        f"\nObservation appended:\n"
        f"  {reception_path} (id={doc.observation_id}, kind={doc.kind})\n"
    )

    if kind == TERMINAL_KIND:
        prior = _count_prior_observations(reception_path) - 1
        _print_silence_memo_skeleton(
            season=args.season,
            week_index=args.week_index,
            version=args.version,
            prior_count=prior,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
