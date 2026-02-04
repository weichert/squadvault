from __future__ import annotations

from pathlib import Path
import re

TARGETS = [
    Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py"),
    Path("src/squadvault/consumers/recap_export_variants_approved.py"),
]

NEEDLE_LINE = 'print("ERROR: No APPROVED WEEKLY_RECAP artifact found for this week. Refusing export.", file=sys.stderr)'
RETURN_LINE = "return 2"

REPLACEMENT_LINES = [
    'print("WARN: No APPROVED WEEKLY_RECAP artifact found for this week. Skipping export.", file=sys.stderr)',
    'if os.environ.get("SV_STRICT_EXPORTS", "0") == "1":',
    "    return 2",
    "return 0",
]

def ensure_import_os(text: str) -> str:
    if re.search(r"(?m)^\s*import\s+os\s*$", text):
        return text
    # Insert near sys import if present
    m = re.search(r"(?m)^\s*import\s+sys\s*$", text)
    if m:
        start = m.start()
        return text[:start] + "import os\n" + text[start:]
    # Otherwise insert after first import/from line
    m = re.search(r"(?m)^(import\s+|from\s+)", text)
    if m:
        line_start = text.rfind("\n", 0, m.start()) + 1
        return text[:line_start] + "import os\n" + text[line_start:]
    return "import os\n" + text

def patch_one(path: Path) -> bool:
    if not path.exists():
        raise SystemExit(f"ERROR: missing target file: {path}")

    s = path.read_text(encoding="utf-8")

    # Idempotency: already patched (warn text + strict gate)
    if "Skipping export." in s and "SV_STRICT_EXPORTS" in s:
        print(f"OK: already patched: {path}")
        return False

    if NEEDLE_LINE not in s:
        raise SystemExit(f"ERROR: needle line not found in {path}")

    # Ensure os import exists before we add os.environ usage
    s2 = ensure_import_os(s)

    # Find the exact needle line and its indentation
    lines = s2.splitlines(True)
    needle_idx = None
    needle_indent = ""
    for i, line in enumerate(lines):
        if NEEDLE_LINE in line:
            needle_idx = i
            needle_indent = re.match(r"^(\s*)", line).group(1)  # type: ignore[union-attr]
            break
    if needle_idx is None:
        raise SystemExit(f"ERROR: could not locate needle line after import adjustments in {path}")

    # Validate there's a return 2 soon after (within next 20 lines)
    search_window = "".join(lines[needle_idx:needle_idx + 20])
    if RETURN_LINE not in search_window:
        raise SystemExit(f"ERROR: expected '{RETURN_LINE}' near needle in {path}; refusing.")

    # Build indented replacement block
    repl = "\n".join(needle_indent + ln if ln else "" for ln in REPLACEMENT_LINES) + "\n"

    # Replace the needle line with the replacement block
    # (keep original line ending behavior by ensuring repl ends with newline)
    new_lines = lines[:]
    # Replace the whole line containing the needle (not just substring)
    old_line = new_lines[needle_idx]
    if old_line.strip() != NEEDLE_LINE:
        # if there is trailing spaces/comments, refuse
        raise SystemExit(f"ERROR: unexpected formatting on needle line in {path}: {old_line!r}")
    new_lines[needle_idx] = repl

    # Remove the *next* 'return 2' line after the inserted block (the old unconditional failure)
    removed_return = False
    for j in range(needle_idx + 1, min(len(new_lines), needle_idx + 40)):
        if new_lines[j].lstrip().startswith(RETURN_LINE):
            # remove that line entirely
            new_lines.pop(j)
            removed_return = True
            break
    if not removed_return:
        raise SystemExit(f"ERROR: failed to remove the old '{RETURN_LINE}' line in {path}; refusing.")

    out = "".join(new_lines)
    if out == s:
        raise SystemExit(f"ERROR: patch produced no changes for {path} (unexpected).")

    path.write_text(out, encoding="utf-8")
    print(f"OK: patched {path}")
    return True

def main() -> None:
    changed = False
    for p in TARGETS:
        changed = patch_one(p) or changed
    if not changed:
        print("OK: no changes needed.")

if __name__ == "__main__":
    main()
