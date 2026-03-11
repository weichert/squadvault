from pathlib import Path

p = Path(".gitignore")
s = p.read_text(encoding="utf-8").splitlines()

needle = "PY"
allow = "!scripts/py"

# confirm the ignore rule exists
if needle not in s:
    raise SystemExit("ERROR: .gitignore missing line 'PY' (expected ignore rule). Refusing to patch.")

# if already allowed, no-op
if allow in s:
    print("OK: .gitignore already allows scripts/py")
    raise SystemExit(0)

# insert allow line immediately after the first exact 'PY' line
out = []
inserted = False
for line in s:
    out.append(line)
    if (not inserted) and line == needle:
        out.append(allow)
        inserted = True

if not inserted:
    raise SystemExit("ERROR: Could not insert allow rule. Refusing.")

p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("OK: patched .gitignore (added !scripts/py after PY)")
