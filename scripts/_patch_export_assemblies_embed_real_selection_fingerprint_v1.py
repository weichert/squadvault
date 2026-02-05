#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")

SENTINEL = "SV_PATCH_EXPORT_ASSEMBLIES_EMBED_REAL_SELECTION_FP_V1"


def _die(msg: str) -> None:
    raise SystemExit(msg)


def main() -> None:
    if not TARGET.exists():
        _die(f"ERROR: missing target: {TARGET}")

    pre = TARGET.read_text(encoding="utf-8")

    if SENTINEL in pre:
        print(f"OK: already patched: {TARGET.name} ({SENTINEL})")
        return

    lines = pre.splitlines(True)

    insert_at = None
    saw_import = False
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            saw_import = True
            continue
        if saw_import and line.strip() == "":
            insert_at = i + 1
            break

    if insert_at is None:
        _die("ERROR: could not locate insertion point after imports")

    helper = f"""\
# {SENTINEL}
# Ensure exported narrative assemblies embed the REAL selection_fingerprint for the week.
# This avoids downstream NAC preflight normalization of placeholder fingerprints.
def _is_placeholder_selection_fp(fp: str) -> bool:
    s = (fp or "").strip()
    if not s:
        return True
    if s in ("__pending__", "__placeholder__"):
        return True
    if set(s) == {{"0"}} and len(s) >= 32:
        return True
    return False


def _fetch_latest_approved_weekly_recap_fp(conn, league_id: str, season: int, week_index: int) -> str:
    \"\"\"Return latest APPROVED WEEKLY_RECAP selection_fingerprint for the week, or '' if not found.\"\"\"
    cur = conn.cursor()
    cur.execute(
        \"\"\"
        SELECT selection_fingerprint
          FROM recap_artifacts
         WHERE league_id=?
           AND season=?
           AND week_index=?
           AND artifact_type='WEEKLY_RECAP'
           AND state='APPROVED'
         ORDER BY version DESC
         LIMIT 1
        \"\"\",
        (str(league_id), int(season), int(week_index)),
    )
    row = cur.fetchone()
    if not row:
        return ""
    try:
        val = row["selection_fingerprint"]
    except Exception:
        val = row[0]
    return str(val or "")


def _effective_selection_fp(conn, league_id: str, season: int, week_index: int, candidate: str) -> str:
    \"\"\"If candidate is missing/placeholder, replace with DB-approved fp; else return candidate.\"\"\"
    if not _is_placeholder_selection_fp(candidate):
        return str(candidate).strip()
    fallback = _fetch_latest_approved_weekly_recap_fp(conn, league_id, season, week_index).strip()
    return fallback or (str(candidate or "").strip())


"""

    lines.insert(insert_at, helper)
    mid = "".join(lines)

    needle = '    selection_fp = str(data.get("selection_fingerprint") or "")\n'
    if needle in mid:
        post = mid.replace(
            needle,
            '    selection_fp = _effective_selection_fp(conn, league_id, season, week_index, str(data.get("selection_fingerprint") or ""))\n',
            1,
        )
    else:
        if 'selection_fp = str(data.get("selection_fingerprint") or "")' not in mid:
            _die("ERROR: could not find expected selection_fp assignment")
        mid_lines = mid.splitlines(True)
        replaced = False
        out = []
        for line in mid_lines:
            if (not replaced) and 'selection_fp = str(data.get("selection_fingerprint") or "")' in line:
                indent = line.split("selection_fp", 1)[0]
                out.append(
                    f'{indent}selection_fp = _effective_selection_fp(conn, league_id, season, week_index, str(data.get("selection_fingerprint") or ""))\n'
                )
                replaced = True
            else:
                out.append(line)
        if not replaced:
            _die("ERROR: replacement failed unexpectedly")
        post = "".join(out)

    if SENTINEL not in post:
        _die("ERROR: postcondition failed: sentinel missing after patch")
    if "_effective_selection_fp(conn, league_id, season, week_index" not in post:
        _die("ERROR: postcondition failed: effective selection fp call missing")

    TARGET.write_text(post, encoding="utf-8")
    print(f"OK: patched {TARGET} (embed real selection_fingerprint into narrative assemblies).")


if __name__ == "__main__":
    main()
