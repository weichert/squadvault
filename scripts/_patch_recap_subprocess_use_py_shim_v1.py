from pathlib import Path

p = Path("scripts/recap.py")
s = p.read_text(encoding="utf-8")

needle_gp = """cmd = [
        sys.executable,
        "-u",
        "scripts/golden_path_recap_lifecycle.py","""

needle_fetch = """cmd = [
        sys.executable,
        "-u",
        "scripts/recap_week_fetch_approved.py","""

if "def cmd_golden_path" not in s:
    raise SystemExit("ERROR: recap.py missing cmd_golden_path. Refusing to patch.")
if "scripts/golden_path_recap_lifecycle.py" not in s:
    raise SystemExit("ERROR: recap.py missing golden_path_recap_lifecycle.py reference. Refusing to patch.")
if "scripts/recap_week_fetch_approved.py" not in s:
    raise SystemExit("ERROR: recap.py missing recap_week_fetch_approved.py reference. Refusing to patch.")

before = s

# Patch golden-path subprocess invocation
if needle_gp not in s:
    raise SystemExit("ERROR: golden-path cmd block not in expected form. Refusing to patch.")
s = s.replace(
    needle_gp,
    """cmd = [
        "./scripts/py",
        "-u",
        "scripts/golden_path_recap_lifecycle.py",""",
    1,
)

# Patch fetch-approved subprocess invocation
if needle_fetch not in s:
    raise SystemExit("ERROR: fetch-approved cmd block not in expected form. Refusing to patch.")
s = s.replace(
    needle_fetch,
    """cmd = [
        "./scripts/py",
        "-u",
        "scripts/recap_week_fetch_approved.py",""",
    1,
)

if s == before:
    raise SystemExit("ERROR: no changes made. Refusing to write.")

p.write_text(s, encoding="utf-8")
print("OK: patched scripts/recap.py subprocess runners to use ./scripts/py (golden-path, fetch-approved)")
