#!/usr/bin/env python3
"""Wednesday digest generator (Track D, Session 2).

Usage:
    ./scripts/py scripts/generate_wednesday_digest.py
    ./scripts/py scripts/generate_wednesday_digest.py --season 2026
"""
from __future__ import annotations
import argparse, glob, json, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SquadVault Wednesday digest")
    p.add_argument("--db", default=str(REPO_ROOT / ".local_squadvault.sqlite"))
    p.add_argument("--season", type=int, default=int(os.environ.get("SQUADVAULT_YEAR", "2025")))
    p.add_argument("--league-id", default=os.environ.get("MFL_LEAGUE_ID", "70985"))
    return p.parse_args()

def read_last_ingest_log() -> dict:
    logs = sorted((REPO_ROOT / "logs").glob("ingest_*.log"), reverse=True)
    if not logs:
        return {"found": False}
    text = logs[0].read_text()
    def find(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else None
    return {
        "found": True,
        "path": logs[0].name,
        "run_at": find(r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\] Starting ingest"),
        "ingest_status": find(r"ingest_status\s*=\s*(\S+)"),
        "events_prepared": find(r"events_prepared\s*=\s*(\d+)"),
        "inserted": find(r"inserted\s*=\s*(\d+)"),
        "skipped": find(r"skipped\s*=\s*(\d+)"),
        "exit_code": find(r"Ingest exited with code\s+(\d+)"),
    }

def query_canonical_counts(conn, league_id, season):
    rows = conn.execute("""
        SELECT event_type, COUNT(*) as n FROM canonical_events
        WHERE league_id=? AND season=? GROUP BY event_type ORDER BY n DESC
    """, (league_id, season)).fetchall()
    return {et: n for et, n in rows}

def query_week_states(conn, league_id, season):
    rows = conn.execute("""
        SELECT week_index, version, state, approved_at
        FROM recap_artifacts WHERE league_id=? AND season=?
        ORDER BY week_index DESC, version DESC
    """, (league_id, season)).fetchall()
    by_week = {}
    for week_index, version, state, approved_at in rows:
        if week_index not in by_week:
            by_week[week_index] = {
                "week_index": week_index, "latest_version": version,
                "latest_state": state, "has_approved": False,
                "approved_version": None, "approved_at": None,
            }
        if state == "APPROVED" and not by_week[week_index]["has_approved"]:
            by_week[week_index]["has_approved"] = True
            by_week[week_index]["approved_version"] = version
            by_week[week_index]["approved_at"] = approved_at
    return sorted(by_week.values(), key=lambda r: r["week_index"], reverse=True)

def query_latest_angles(conn, league_id, season):
    row = conn.execute("""
        SELECT id, week_index, attempt, angles_summary_json,
               budgeted_summary_json, captured_at
        FROM prompt_audit WHERE league_id=? AND season=?
        ORDER BY id DESC LIMIT 1
    """, (league_id, season)).fetchone()
    if not row:
        return None
    aid, week_index, attempt, angles_json, budgeted_json, captured_at = row
    def counts(j):
        d = {}
        for e in (json.loads(j) if j else []):
            c = e.get("category", "UNKNOWN")
            d[c] = d.get(c, 0) + 1
        return d
    return {
        "audit_id": aid, "week_index": week_index, "attempt": attempt,
        "captured_at": captured_at,
        "detected": counts(angles_json), "budgeted": counts(budgeted_json),
    }

def read_reception(season):
    files = sorted(glob.glob(str(REPO_ROOT / f"archive/recaps/{season}/*reception.yaml")), reverse=True)  # SV_ALLOW_UNSORTED_FS_ORDER
    obs = []
    for fpath in files:
        text = Path(fpath).read_text()
        fname = Path(fpath).name
        for block in text.split("---"):
            block = block.strip()
            if not block:
                continue
            o = {"source_file": fname}
            for line in block.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    o[k.strip()] = v.strip().strip('"')  
            if "observation_id" in o:
                obs.append(o)
    return obs

def recommended_action(w):
    if w["latest_state"] == "APPROVED":
        return "Ready to distribute (latest version is APPROVED)."
    if w["latest_state"] == "DRAFT" and w["has_approved"]:
        return (f"Newer draft v{w['latest_version']} above approved v{w['approved_version']}. "
                f"Review draft or distribute approved version.")
    if w["latest_state"] == "DRAFT":
        return f"Draft v{w['latest_version']} pending review. No approved version yet."
    if w["latest_state"] == "WITHHELD":
        return f"Latest v{w['latest_version']} withheld. Check withheld_reason."
    return "Unknown state -- inspect manually."

def render(args, log, counts, weeks, angles, reception):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    L = []
    L.append(f"# SquadVault Wednesday Digest -- {args.season} Season")
    L.append(f"Generated: {now}")
    L.append(f"League: {args.league_id}  DB: {Path(args.db).name}")
    L.append("")
    L.append("---")
    L.append("## Ingest Status")
    L.append("")
    if not log["found"]:
        L.append("No ingest log found. Run scripts/run_weekly_ingest.sh first.")
    else:
        flag = "OK" if log.get("exit_code") == "0" else "ERROR"
        L.append(f"Last run:        {log['run_at']}")
        L.append(f"Ingest status:   {log['ingest_status']} (exit {log['exit_code']}) [{flag}]")
        L.append(f"Events:          prepared={log['events_prepared']}  inserted={log['inserted']}  skipped={log['skipped']}")
    L.append("")
    L.append("---")
    L.append(f"## Canonical Events ({args.season} Season)")
    L.append("")
    if counts:
        for et, n in counts.items():
            L.append(f"  {et}: {n}")
    else:
        L.append("No canonical events found.")
    L.append("")
    L.append("---")
    L.append("## Recap Artifact Status")
    L.append("")
    if not weeks:
        L.append("No recap artifacts found for this season.")
    else:
        cur = weeks[0]
        L.append(f"Current week:     W{cur['week_index']}")
        L.append(f"Latest artifact:  v{cur['latest_version']} ({cur['latest_state']})")
        if cur["has_approved"]:
            L.append(f"Approved:         v{cur['approved_version']} at {cur['approved_at']}")
        L.append(f"Recommended:      {recommended_action(cur)}")
        L.append("")
        L.append("Recent weeks:")
        for w in weeks[:8]:
            note = f" [approved v{w['approved_version']}]" if w["has_approved"] else ""
            L.append(f"  W{w['week_index']:02d}  v{w['latest_version']} ({w['latest_state']}){note}")
    L.append("")
    L.append("---")
    L.append("## Narrative Angles (most recent audit)")
    L.append("")
    if not angles:
        L.append("No prompt_audit rows found for this season.")
    else:
        L.append(f"Audit id={angles['audit_id']}  W{angles['week_index']}  attempt={angles['attempt']}  captured={angles['captured_at']}")
        L.append("")
        L.append("Detected:")
        for cat, n in sorted(angles["detected"].items()):
            L.append(f"  {cat}: {n}")
        L.append("")
        L.append("Budgeted (after budget loop):")
        for cat, n in sorted(angles["budgeted"].items()):
            L.append(f"  {cat}: {n}")
        evicted = set(angles["detected"]) - set(angles["budgeted"])
        if evicted:
            L.append("")
            L.append(f"Evicted by budget: {', '.join(sorted(evicted))}")
    L.append("")
    L.append("---")
    L.append("## Prior Reception")
    L.append("")
    if not reception:
        L.append("No reception observations on file.")
    else:
        L.append(f"{len(reception)} observation(s):")
        L.append("")
        for o in reception:
            L.append(f"  [{o.get('source_file','')}] {o.get('member','?')} ({o.get('kind','')}): {o.get('content','')}")
    L.append("")
    L.append("---")
    return "\n".join(L) + "\n"

def main() -> int:
    args = parse_args()
    log = read_last_ingest_log()
    conn = sqlite3.connect(args.db)
    counts = query_canonical_counts(conn, args.league_id, args.season)
    weeks = query_week_states(conn, args.league_id, args.season)
    angles = query_latest_angles(conn, args.league_id, args.season)
    conn.close()
    reception = read_reception(args.season)
    print(render(args, log, counts, weeks, angles, reception))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
