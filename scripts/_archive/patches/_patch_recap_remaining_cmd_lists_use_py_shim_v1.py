from pathlib import Path

p = Path("scripts/recap.py")
s = p.read_text(encoding="utf-8")

def must_contain(needle: str) -> None:
    if needle not in s:
        raise SystemExit(f"ERROR: expected snippet not found (refusing to patch): {needle}")

# --- A) cmd_export_assemblies: switch to ./scripts/py and remove PYTHONPATH env injection ---
old_export_assemblies = """    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_export_narrative_assemblies_approved.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--export-dir", args.export_dir,
    ]

    env = dict(**os.environ)
    env["PYTHONPATH"] = "src" + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    proc = subprocess.run(cmd, env=env)
    return int(proc.returncode)
"""

new_export_assemblies = """    cmd = [
        "./scripts/py",
        "-u",
        "src/squadvault/consumers/recap_export_narrative_assemblies_approved.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--export-dir", args.export_dir,
    ]

    proc = subprocess.run(cmd)
    return int(proc.returncode)
"""

must_contain(old_export_assemblies)

# --- B) cmd_render_week: switch to ./scripts/py ---
old_render_week = """    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_week_render.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
    ]"""

new_render_week = """    cmd = [
        "./scripts/py",
        "-u",
        "src/squadvault/consumers/recap_week_render.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
    ]"""

must_contain(old_render_week)

# --- C) cmd_withhold: switch to ./scripts/py ---
old_withhold = """    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_artifact_withhold.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--version", str(args.version),
        "--reason", args.reason,
    ]"""

new_withhold = """    cmd = [
        "./scripts/py",
        "-u",
        "src/squadvault/consumers/recap_artifact_withhold.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--version", str(args.version),
        "--reason", args.reason,
    ]"""

must_contain(old_withhold)

before = s
s = s.replace(old_export_assemblies, new_export_assemblies, 1)
s = s.replace(old_render_week, new_render_week, 1)
s = s.replace(old_withhold, new_withhold, 1)

if s == before:
    raise SystemExit("ERROR: no changes made (unexpected).")

p.write_text(s, encoding="utf-8")
print("OK: patched scripts/recap.py remaining sys.executable cmd lists to ./scripts/py (and removed PYTHONPATH env injection in export-assemblies)")
