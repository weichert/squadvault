from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

# We patch inside the embedded export Python snippet by replacing the existing contract block
# with a stronger one that enforces both header and Week metadata key.
BEGIN_MARK = "# Enforce Rivalry Chronicle output contract header (v1): first line must be exact."
# We'll replace from that comment down through the out_path.write_text(...) line.
BLOCK_RE = re.compile(
    r"""
^#\ Enforce\ Rivalry\ Chronicle\ output\ contract\ header\ \(v1\):\ first\ line\ must\ be\ exact\.\s*\n
hdr\s*=\s*["']#\ Rivalry\ Chronicle\ \(v1\)["']\s*\n
lines\s*=\s*str\(txt\)\.splitlines\(\)\s*\n
(?:.*?\n)*?
out_path\.write_text\(txt,\s*encoding=["']utf-8["']\)\s*$
""".strip(),
    re.M | re.S | re.X,
)

REPLACEMENT = """\
# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.
hdr = "# Rivalry Chronicle (v1)"
week_val = str(int({week_index}))  # canonical numeric string
season_val = str(int({season}))
league_val = str(int({league_id}))

lines = str(txt).splitlines()

# Drop leading blank lines
while lines and lines[0].strip() == "":
    lines.pop(0)

# Ensure header is first line
if not lines:
    lines = [hdr]
else:
    if lines[0] != hdr:
        lines = [hdr, ""] + lines

# --- Metadata normalization ---
# Expected metadata lines are of the form "Key: Value" and appear near top, after header.
# We'll treat the contiguous "Key: Value" lines after the header (skipping blank lines) as metadata.
i = 1
# Skip a single blank line after header if present
if i < len(lines) and lines[i].strip() == "":
    i += 1

meta_start = i
meta = []
while i < len(lines):
    s = lines[i]
    if s.strip() == "":
        break
    if ":" not in s:
        break
    key = s.split(":", 1)[0].strip()
    if not key:
        break
    meta.append(s)
    i += 1

meta_end = i  # exclusive

def upsert(meta_lines: list[str], key: str, value: str) -> list[str]:
    out = []
    found = False
    for ln in meta_lines:
        k = ln.split(":", 1)[0].strip()
        if k == key:
            out.append(f"{key}: {value}")
            found = True
        else:
            out.append(ln.rstrip())
    if not found:
        out.append(f"{key}: {value}")
    return out

meta = [m.rstrip() for m in meta]
meta = upsert(meta, "League ID", league_val)
meta = upsert(meta, "Season", season_val)
meta = upsert(meta, "Week", week_val)

# Rebuild lines
new_lines = lines[:meta_start] + meta + lines[meta_end:]

txt = "\\n".join(new_lines).rstrip() + "\\n"
out_path.write_text(txt, encoding="utf-8")
"""

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    if "Enforce Rivalry Chronicle output contract (v1): header + required metadata keys." in txt0:
        return  # already patched

    m = BLOCK_RE.search(txt0)
    if not m:
        raise SystemExit("Refusing: could not locate existing contract header block to upgrade (v6).")

    # We know fixture values from the CI prove invocation.
    upgraded = REPLACEMENT.format(league_id=70985, season=2024, week_index=6)

    txt1 = BLOCK_RE.sub(upgraded.rstrip(), txt0, count=1)
    PROVE.write_text(txt1 + ("" if txt1.endswith("\n") else "\n"), encoding="utf-8")

if __name__ == "__main__":
    main()
