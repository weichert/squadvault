from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

HDR_LINE = 'hdr = "# Rivalry Chronicle (v1)"'
WRITE_LINE = 'out_path.write_text(txt, encoding="utf-8")'

LEAGUE_ID = 70985
SEASON = 2024
WEEK_INDEX = 6

REPLACEMENT_LINES = [
    '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.',
    'hdr = "# Rivalry Chronicle (v1)"',
    f'league_val = "{LEAGUE_ID}"',
    f'season_val = "{SEASON}"',
    f'week_val = "{WEEK_INDEX}"',
    '',
    'lines = str(txt).splitlines()',
    '',
    '# Drop leading blank lines',
    'while lines and lines[0].strip() == "":',
    '    lines.pop(0)',
    '',
    '# Ensure header is first line',
    'if not lines:',
    '    lines = [hdr]',
    'else:',
    '    if lines[0] != hdr:',
    '        lines = [hdr, ""] + lines',
    '',
    '# --- Metadata normalization ---',
    '# Treat contiguous "Key: Value" lines after header (optionally after one blank line) as metadata.',
    'i = 1',
    'if i < len(lines) and lines[i].strip() == "":',
    '    i += 1',
    'meta_start = i',
    'meta = []',
    'while i < len(lines):',
    '    s = lines[i]',
    '    if s.strip() == "":',
    '        break',
    '    if ":" not in s:',
    '        break',
    '    key = s.split(":", 1)[0].strip()',
    '    if not key:',
    '        break',
    '    meta.append(s.rstrip())',
    '    i += 1',
    'meta_end = i',
    '',
    'def upsert(meta_lines: list[str], key: str, value: str) -> list[str]:',
    '    out = []',
    '    found = False',
    '    for ln in meta_lines:',
    '        k = ln.split(":", 1)[0].strip()',
    '        if k == key:',
    '            out.append(f"{key}: {value}")',
    '            found = True',
    '        else:',
    '            out.append(ln.rstrip())',
    '    if not found:',
    '        out.append(f"{key}: {value}")',
    '    return out',
    '',
    'meta = upsert(meta, "League ID", league_val)',
    'meta = upsert(meta, "Season", season_val)',
    'meta = upsert(meta, "Week", week_val)',
    '',
    'new_lines = lines[:meta_start] + meta + lines[meta_end:]',
    'txt = "\\n".join(new_lines).rstrip() + "\\n"',
    'out_path.write_text(txt, encoding="utf-8")',
]

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")
    lines = txt0.splitlines(True)  # keepends

    hdr_idxs = [i for i, ln in enumerate(lines) if HDR_LINE in ln]
    if len(hdr_idxs) != 1:
        raise SystemExit(f"Refusing: expected exactly 1 HDR_LINE match, found {len(hdr_idxs)}.")

    write_idxs = [i for i, ln in enumerate(lines) if WRITE_LINE in ln]
    if len(write_idxs) != 1:
        raise SystemExit(f"Refusing: expected exactly 1 WRITE_LINE match, found {len(write_idxs)}.")

    hdr_i = hdr_idxs[0]
    write_i = write_idxs[0]
    if write_i <= hdr_i:
        raise SystemExit("Refusing: write_text appears before hdr anchor; unexpected structure.")

    # Start replacement at nearest preceding comment line if it looks like the contract block,
    # otherwise start at hdr line itself.
    start_i = hdr_i
    for j in range(hdr_i - 1, max(-1, hdr_i - 15), -1):
        if lines[j].lstrip().startswith("# Enforce Rivalry Chronicle"):
            start_i = j
            break

    # Replace through the out_path.write_text line (inclusive).
    end_i = write_i

    replacement = "\n".join(REPLACEMENT_LINES) + "\n"

    out = []
    out.extend(lines[:start_i])
    out.append(replacement)
    out.extend(lines[end_i + 1:])

    txt1 = "".join(out)
    if txt1 != txt0:
        PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
