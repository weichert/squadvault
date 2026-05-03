"""Export approved narrative assemblies to disk."""

#!/usr/bin/env python3
from __future__ import annotations

from squadvault.core.storage.session import DatabaseSession


# SV_PATCH_EXPORT_ASSEMBLIES_EMBED_REAL_SELECTION_FP_V1
# Ensure exported narrative assemblies embed the REAL selection_fingerprint for the week.
# This avoids downstream NAC preflight normalization of placeholder fingerprints.
def _is_placeholder_selection_fp(fp: str) -> bool:
    """Return True if fingerprint is a placeholder value."""
    s = (fp or "").strip()
    if not s:
        return True
    if s in ("__pending__", "__placeholder__"):
        return True
    if set(s) == {"0"} and len(s) >= 32:
        return True
    return False


def _fetch_latest_approved_weekly_recap_fp(conn, league_id: str, season: int, week_index: int) -> str:
    """Return latest APPROVED WEEKLY_RECAP selection_fingerprint for the week, or '' if not found."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT selection_fingerprint
          FROM recap_artifacts
         WHERE league_id=?
           AND season=?
           AND week_index=?
           AND artifact_type='WEEKLY_RECAP'
           AND state='APPROVED'
         ORDER BY version DESC
         LIMIT 1
        """,
        (str(league_id), int(season), int(week_index)),
    )
    row = cur.fetchone()
    if not row:
        return ""
    try:
        val = row["selection_fingerprint"]
    except Exception as exc:
        logger.debug("%s", exc)
        val = row[0]
    return str(val or "")


def _effective_selection_fp(conn, league_id: str, season: int, week_index: int, candidate: str) -> str:
    """If candidate is missing/placeholder, replace with DB-approved fp; else return candidate."""
    if not _is_placeholder_selection_fp(candidate):
        return str(candidate).strip()
    fallback = _fetch_latest_approved_weekly_recap_fp(conn, league_id, season, week_index).strip()
    return fallback or (str(candidate or "").strip())


import argparse
import json
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
# SV_PATCH_EXPORT_ASSEMBLIES_REMOVE_HEX64_RE_V4_ARTIFACT_V6

BANNER = (
    "NON-CANONICAL — Narrative Assembly Export\n"
    "Derived strictly from an APPROVED recap artifact. No new facts. No inference. No personalization.\n"
)

MARKERS = {
    "FACTS": ("<!-- BEGIN_CANONICAL_FACTS -->", "<!-- END_CANONICAL_FACTS -->"),
    "WINDOW": ("<!-- BEGIN_CANONICAL_WINDOW -->", "<!-- END_CANONICAL_WINDOW -->"),
    "FINGERPRINT": ("<!-- BEGIN_CANONICAL_FINGERPRINT -->", "<!-- END_CANONICAL_FINGERPRINT -->"),
    "COUNTS": ("<!-- BEGIN_CANONICAL_COUNTS -->", "<!-- END_CANONICAL_COUNTS -->"),
    "TRACE": ("<!-- BEGIN_CANONICAL_TRACE -->", "<!-- END_CANONICAL_TRACE -->"),
    "WRITING_ROOM": ("<!-- BEGIN_WRITING_ROOM_SELECTION_SET_V1 -->", "<!-- END_WRITING_ROOM_SELECTION_SET_V1 -->"),
}

ALLOWED_HEADINGS = {
    "## Provenance",
    "## What happened (facts) — canonical",
    "## Counts — canonical",
    "## Traceability — canonical",
    "## Window — canonical",
    "## Notes (non-canonical)",
    "## Writing Room (SelectionSetV1)",
}


@dataclass(frozen=True)
class ApprovedArtifact:
    league_id: str
    season: int
    week_index: int
    version: int
    selection_fingerprint: str
    window_start: str
    window_end: str
    rendered_text: str  # canonical facts block as stored


def fetch_approved_weekly_recap(db: str, league_id: str, season: int, week_index: int) -> ApprovedArtifact | None:
    """Fetch approved WEEKLY_RECAP artifact from DB."""
    with DatabaseSession(db) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM recap_artifacts
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = 'WEEKLY_RECAP'
              AND state = 'APPROVED'
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, int(season), int(week_index)),
        )
        row = cur.fetchone()
    if row is None:
        return None

    return ApprovedArtifact(
        league_id=str(row["league_id"]),
        season=int(row["season"]),
        week_index=int(row["week_index"]),
        version=int(row["version"]),
        selection_fingerprint=str(row["selection_fingerprint"] or ""),
        window_start=str(row["window_start"] or ""),
        window_end=str(row["window_end"] or ""),
        rendered_text=str(row["rendered_text"] or ""),
    )


def _load_recap_runs_for_artifact(
    db_path: str, league_id: str, season: int, week_index: int
) -> dict[str, Any] | None:
    """
    Load the recap_runs row corresponding to (league, season, week).

    Returns the row as a plain dict, or None if no row exists. Treats
    None/empty/whitespace as absent for canonical_ids_json and
    counts_by_type_json — the absence-Note path uses this signal to
    distinguish "no row recorded" from "recorded with zero events".
    """
    with DatabaseSession(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT canonical_ids_json, counts_by_type_json
              FROM recap_runs
             WHERE league_id=?
               AND season=?
               AND week_index=?
             ORDER BY id DESC
             LIMIT 1
            """,
            (str(league_id), int(season), int(week_index)),
        )
        row = cur.fetchone()
    if row is None:
        return None
    try:
        return {
            "canonical_ids_json": row["canonical_ids_json"],
            "counts_by_type_json": row["counts_by_type_json"],
        }
    except (KeyError, IndexError):
        return None


def _is_present_json(raw: Any) -> bool:
    """True if a JSON column is populated; False if NULL/empty/whitespace."""
    if raw is None:
        return False
    s = str(raw).strip()
    return bool(s)


def _render_counts_body(recap_run: dict[str, Any] | None) -> str:
    """
    Render the COUNTS block body.

    When counts_by_type_json is populated (including '{}' for "recorded with
    zero events"): emit `Events selected: N\\n` plus optional `Breakdown:` lines.
    When absent (None row, NULL field, or empty string): emit a documented
    absence-Note. NAC checker imposes no content shape on COUNTS body.
    """
    if recap_run is None or not _is_present_json(recap_run.get("counts_by_type_json")):
        return (
            "Note: counts unavailable for this artifact "
            "(recap_runs.counts_by_type_json absent or empty).\n"
        )

    raw = recap_run.get("counts_by_type_json")
    try:
        counts = json.loads(str(raw)) or {}
    except (ValueError, TypeError):
        return (
            "Note: counts unavailable for this artifact "
            "(recap_runs.counts_by_type_json not valid JSON).\n"
        )

    if not isinstance(counts, dict):
        return (
            "Note: counts unavailable for this artifact "
            "(recap_runs.counts_by_type_json is not a JSON object).\n"
        )

    total = 0
    for v in counts.values():
        try:
            total += int(v)
        except (ValueError, TypeError):
            continue

    lines = [f"Events selected: {total}"]
    if counts:
        lines.append("")
        lines.append("Breakdown:")
        for k in sorted(counts.keys()):
            lines.append(f"  - {k}: {counts[k]}")
    return "\n".join(lines) + "\n"


def _render_trace_body(recap_run: dict[str, Any] | None) -> str:
    """
    Render the TRACE block body.

    NAC checker (Tests/_nac_check_assembly_plain_v1.py) requires the literal
    label `Trace (canonical_event ids):` inside the TRACE block. The label is
    always emitted as the first line; the lines beneath it are either the
    canonical_event ids, `(none)` for the empty-but-recorded case, or a
    documented absence-Note when canonical_ids_json is absent.
    """
    label = "Trace (canonical_event ids):"
    if recap_run is None or not _is_present_json(recap_run.get("canonical_ids_json")):
        return (
            f"{label}\n"
            f"Note: trace unavailable for this artifact "
            f"(recap_runs.canonical_ids_json absent or empty).\n"
        )

    raw = recap_run.get("canonical_ids_json")
    try:
        ids = json.loads(str(raw)) or []
    except (ValueError, TypeError):
        return (
            f"{label}\n"
            f"Note: trace unavailable for this artifact "
            f"(recap_runs.canonical_ids_json not valid JSON).\n"
        )

    if not isinstance(ids, list):
        return (
            f"{label}\n"
            f"Note: trace unavailable for this artifact "
            f"(recap_runs.canonical_ids_json is not a JSON array).\n"
        )

    if not ids:
        return f"{label}\n  (none)\n"

    lines = [label]
    chunk: list[str] = []
    for cid in ids:
        chunk.append(str(cid))
        if len(chunk) >= 25:
            lines.append("  " + ", ".join(chunk))
            chunk = []
    if chunk:
        lines.append("  " + ", ".join(chunk))
    return "\n".join(lines) + "\n"


def build_canonical_blocks(approved: ApprovedArtifact, db_path: str) -> dict[str, str]:
    """
    Build the four canonical blocks (WINDOW, FINGERPRINT, COUNTS, TRACE) from
    structured fields on the APPROVED artifact and from recap_runs, without
    parsing rendered_text.

    Replaces extract_blocks_from_neutral. The previous parse-text approach
    coupled the export to a renderer-output shape that fixture rows did not
    conform to (see _observations/OBSERVATIONS_2026_05_02_EXPORT_ASSEMBLIES_PARSER_FAILURE_POST_D50A2A7.md).
    Building from structured fields decouples export shape from any single
    text-rendering format, and honors silence-preferred-over-speculation:
    when underlying COUNTS/TRACE data is absent, the export emits a documented
    absence-Note inside the canonical markers rather than fabricating values
    or raising.
    """
    # WINDOW — from approved structured fields. The renderer uses an arrow
    # joiner between start and end; preserved here for output-shape parity.
    window_block = f"Window: {approved.window_start} → {approved.window_end}\n"

    # FINGERPRINT — from approved.selection_fingerprint when it is real
    # 64-lower-hex. The downstream NAC checker requires 64-hex; if the field
    # is malformed we still emit the canonical line (downstream fingerprint
    # preflight in prove_golden_path.sh handles known placeholders).
    fp = (approved.selection_fingerprint or "").strip()
    fingerprint_block = f"Selection fingerprint: {fp}\n"

    # COUNTS / TRACE — from recap_runs, with documented absence-Notes when the
    # corresponding JSON field is NULL/empty.
    recap_run = _load_recap_runs_for_artifact(
        db_path, approved.league_id, approved.season, approved.week_index
    )
    counts_block = _render_counts_body(recap_run)
    trace_block = _render_trace_body(recap_run)

    return {
        "WINDOW": window_block,
        "FINGERPRINT": fingerprint_block,
        "COUNTS": counts_block,
        "TRACE": trace_block,
    }


def wrap(marker_key: str, content: str) -> str:
    """Wrap content in begin/end markers for a block."""
    b, e = MARKERS[marker_key]
    return f"{b}\n{content.rstrip()}\n{e}\n"


def _extract_between(text: str, begin: str, end: str) -> str:
    """Extract text between begin and end markers."""
    bi = text.find(begin)
    if bi < 0:
        raise RuntimeError(f"missing marker: {begin}")
    ei = text.find(end)
    if ei < 0:
        raise RuntimeError(f"missing marker: {end}")
    if ei < bi:
        raise RuntimeError(f"marker order invalid: {begin} before {end}")
    body = text[bi + len(begin):ei]
    if body.startswith("\n"):
        body = body[1:]
    if body.endswith("\n"):
        body = body[:-1]
    return body + "\n"


def validate_outside_text_allowlist(full_text: str, allowed_outside_lines: tuple[str, ...]) -> None:
    """Validate no unexpected text exists outside marked blocks."""
    scrubbed = full_text
    for k, (b, e) in MARKERS.items():
        bi = scrubbed.find(b)
        ei = scrubbed.find(e)
        if bi < 0 or ei < 0:
            raise RuntimeError(f"missing markers for {k} during allowlist validation")
        ei2 = ei + len(e)
        scrubbed = scrubbed[:bi] + f"{b}\n{e}\n" + scrubbed[ei2:]

    allowed_set = set(allowed_outside_lines)
    for raw in scrubbed.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line in allowed_set:
            continue
        if line in ALLOWED_HEADINGS:
            continue
        # allow any block markers we use (canonical + writing room)
        if line.startswith("<!-- BEGIN_") or line.startswith("<!-- END_"):
            continue
        raise RuntimeError(f"Unexpected outside-block line (NAC violation): {line}")


def validate_protected_blocks_byte_stable(full_text: str, sources: dict[str, str]) -> None:
    """Validate protected blocks are byte-identical to sources."""
    for key, (b, e) in MARKERS.items():
        extracted = _extract_between(full_text, b, e)
        src = sources[key].rstrip("\n") + "\n"
        if extracted != src:
            raise RuntimeError(f"Protected block mismatch for {key} (byte-stability violation)")


def writing_room_selection_set_v1_path(base: str, league_id: str, season: int, week_index: int) -> Path:
    """
    Deterministic default path for Writing Room SelectionSetV1 side-artifact.
    File-only side artifact: may or may not exist.
    """
    return (
        Path(base)
        / "writing_room"
        / str(league_id)
        / str(season)
        / f"week_{int(week_index):02d}"
        / "selection_set_v1.json"
    )


def _safe_get_list(d: dict[str, Any], k: str) -> list:
    """Safely get a list value from a dict."""
    v = d.get(k, [])
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return []


def _summarize_selection_set_v1(data: dict[str, Any], db_path: str, league_id: str, season: int, week_index: int) -> str:
    """
    Deterministic, non-volatile summary.
    - No timestamps emitted.
    - Derived counters sorted lexicographically.
    """
    selection_set_id = str(data.get("selection_set_id") or "")
    with DatabaseSession(db_path) as conn:
        selection_fp = _effective_selection_fp(conn, league_id, season, week_index, str(data.get("selection_fingerprint") or ""))
    # SV_PATCH_EXPORT_ASSEMBLIES_FORCE_DATA_SELECTION_FP_V2
    # Force real selection_fingerprint back into data for all downstream render paths.
    data['selection_fingerprint'] = selection_fp

    withheld = bool(data.get("withheld", False))
    withheld_reason = data.get("withheld_reason")

    included = _safe_get_list(data, "included_signal_ids")
    excluded = _safe_get_list(data, "excluded")

    reason_codes = []
    for e in excluded:
        if isinstance(e, dict):
            rc = e.get("reason_code")
            if rc is not None:
                reason_codes.append(str(rc))
    c = Counter(reason_codes)

    out: list[str] = []
    if selection_set_id:
        out.append(f"- selection_set_id: {selection_set_id}")
    if selection_fp:
        out.append(f"- selection_fingerprint: {selection_fp}")
    out.append(f"- withheld: {str(withheld).lower()}")
    if withheld and withheld_reason:
        out.append(f"- withheld_reason: {withheld_reason}")
    out.append(f"- included_count: {len(included)}")
    out.append(f"- excluded_count: {len(excluded)}")

    if c:
        out.append("")
        out.append("excluded_by_reason:")
        for k in sorted(c.keys()):
            out.append(f"- {k}: {c[k]}")

    return "\n".join(out).rstrip() + "\n"


def load_writing_room_block_or_not_available(base: str, league_id: str, season: int, week_index: int, *, db_path: str = "") -> str:
    """
    Non-blocking: never fails export. Always returns a deterministic block.
    """
    p = writing_room_selection_set_v1_path(base, league_id, season, week_index)
    if not p.exists():
        return "Not available\n"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return "Not available\n"
        return _summarize_selection_set_v1(data, db_path=db_path, league_id=league_id, season=season, week_index=week_index)
    except Exception as exc:
        logger.debug("%s", exc)
        return "Not available\n"


def assemble_plain_v1(a: ApprovedArtifact, blocks: dict[str, str], writing_room_block: str) -> str:
    """Assemble a plain text narrative from approved artifact and blocks."""
    out = []
    out.append(BANNER.rstrip("\n"))
    out.append("")
    out.append("## Provenance")
    out.append(f"Approved artifact: league={a.league_id} season={a.season} week={a.week_index} approved_version=v{a.version:02d}")
    out.append("")
    out.append("## Writing Room (SelectionSetV1)")
    out.append(wrap("WRITING_ROOM", writing_room_block).rstrip("\n"))
    out.append("")
    out.append("## Window — canonical")
    out.append(wrap("WINDOW", blocks["WINDOW"]).rstrip("\n"))
    out.append("")
    out.append(wrap("FINGERPRINT", blocks["FINGERPRINT"]).rstrip("\n"))
    out.append("")
    out.append("## What happened (facts) — canonical")
    out.append(wrap("FACTS", a.rendered_text).rstrip("\n"))
    out.append("")
    out.append("## Counts — canonical")
    out.append(wrap("COUNTS", blocks["COUNTS"]).rstrip("\n"))
    out.append("")
    out.append("## Traceability — canonical")
    out.append(wrap("TRACE", blocks["TRACE"]).rstrip("\n"))
    out.append("")
    return "\n".join(out).rstrip() + "\n"


def assemble_sharepack_v1(a: ApprovedArtifact, blocks: dict[str, str], writing_room_block: str) -> str:
    """Assemble a sharepack narrative from approved artifact and blocks."""
    out = []
    out.append(BANNER.rstrip("\n"))
    out.append("")
    out.append("## Provenance")
    out.append(f"Approved artifact: league={a.league_id} season={a.season} week={a.week_index} approved_version=v{a.version:02d}")
    out.append("Two fingerprints follow: the Writing Room SelectionSet fingerprint (derived) and the Canonical Recap Selection fingerprint (approved).")
    out.append("")
    out.append("## Writing Room (SelectionSetV1)")
    out.append(wrap("WRITING_ROOM", writing_room_block).rstrip("\n"))
    out.append("")
    out.append(wrap("FINGERPRINT", blocks["FINGERPRINT"]).rstrip("\n"))
    out.append("")
    out.append("## What happened (facts) — canonical")
    out.append(wrap("FACTS", a.rendered_text).rstrip("\n"))
    out.append("")
    out.append("## Counts — canonical")
    out.append(wrap("COUNTS", blocks["COUNTS"]).rstrip("\n"))
    out.append("")
    out.append("## Traceability — canonical")
    out.append(wrap("TRACE", blocks["TRACE"]).rstrip("\n"))
    out.append("")
    out.append("## Window — canonical")
    out.append(wrap("WINDOW", blocks["WINDOW"]).rstrip("\n"))
    out.append("")
    return "\n".join(out).rstrip() + "\n"


def export_dir(base: str, league_id: str, season: int, week_index: int) -> Path:
    """Compute export directory path for a week."""
    return Path(base) / "exports" / str(league_id) / str(season) / f"week_{int(week_index):02d}"


def main(argv: list[str]) -> int:
    """CLI entrypoint: export approved narrative assemblies."""
    ap = argparse.ArgumentParser(
        description="Phase 2.3: Export deterministic narrative assemblies from APPROVED recap artifacts (export-only)"
    )
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--export-dir", default="artifacts", help="Export root (default: artifacts)")
    args = ap.parse_args(argv)

    approved = fetch_approved_weekly_recap(args.db, args.league_id, args.season, args.week_index)
    if approved is None:
        print("WARN: No APPROVED WEEKLY_RECAP artifact found for this week. Skipping export.", file=sys.stderr)
        if os.environ.get("SV_STRICT_EXPORTS", "0") == "1":
            return 2
        return 0

    if not approved.rendered_text.strip():
        print("ERROR: Approved artifact rendered_text is empty (facts block missing). Refusing export.", file=sys.stderr)
        return 3

    blocks = build_canonical_blocks(approved, args.db)


    writing_room_block = load_writing_room_block_or_not_available(
        args.export_dir,
        approved.league_id,
        approved.season,
        approved.week_index,
        db_path=args.db,
    )

    out_plain = assemble_plain_v1(approved, blocks, writing_room_block=writing_room_block)
    out_share = assemble_sharepack_v1(approved, blocks, writing_room_block=writing_room_block)

    sources = {
        "FACTS": approved.rendered_text,
        "WINDOW": blocks["WINDOW"],
        "FINGERPRINT": blocks["FINGERPRINT"],
        "COUNTS": blocks["COUNTS"],
        "TRACE": blocks["TRACE"],
        "WRITING_ROOM": writing_room_block,
    }

    allowed_plain = (
        "NON-CANONICAL — Narrative Assembly Export",
        "Derived strictly from an APPROVED recap artifact. No new facts. No inference. No personalization.",
        f"Approved artifact: league={approved.league_id} season={approved.season} week={approved.week_index} approved_version=v{approved.version:02d}",
    )
    allowed_share = allowed_plain + (
        "Two fingerprints follow: the Writing Room SelectionSet fingerprint (derived) and the Canonical Recap Selection fingerprint (approved).",
    )

    validate_outside_text_allowlist(out_plain, allowed_plain)
    validate_outside_text_allowlist(out_share, allowed_share)
    validate_protected_blocks_byte_stable(out_plain, sources)
    validate_protected_blocks_byte_stable(out_share, sources)

    out_dir = export_dir(args.export_dir, approved.league_id, approved.season, approved.week_index)
    out_dir.mkdir(parents=True, exist_ok=True)

    p_plain = out_dir / f"assembly_plain_v1__approved_v{approved.version:02d}.md"
    p_share = out_dir / f"assembly_sharepack_v1__approved_v{approved.version:02d}.md"

    p_plain.write_text(out_plain, encoding="utf-8")
    p_share.write_text(out_share, encoding="utf-8")

    print(str(p_plain))
    print(str(p_share))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
