from __future__ import annotations

from pathlib import Path

TARGETS = [
    Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py"),
    Path("src/squadvault/consumers/recap_export_variants_approved.py"),
]

NEEDLE_LINE = 'print("ERROR: No APPROVED WEEKLY_RECAP artifact found for this week. Refusing export.", file=sys.stderr)'
RETURN_LINE = "return 2"

REPLACEMENT_BLOCK = """\
print("WARN: No APPROVED WEEKLY_RECAP artifact found for this week. Skipping export.", file=sys.stderr)
if os.environ.get("SV_STRICT_EXPORTS", "0") == "1":
    return 2
return 0
"""

def ensure_import_os(text: str) -> str:
    # Add `import os` if not present.
    # Keep it simple: insert near other imports.
    if "\nimport os\n" in text or text.startswith("import os\n") or "\nimport os\r\n" in text:
        return text
    if "import sys" in text:
        return text.replace("import sys", "import os\nimport sys", 1)
    # Fallback: insert after the first import line.
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            lines.insert(i, "import os\n")
            return "".join(lines)
    # As last resort, prepend.
    return "import os\n" + text

def patch_one(path: Path) -> bool:
    if not path.exists():
        raise SystemExit(f"ERROR: missing target file: {path}")

    s = path.read_text(encoding="utf-8")

    # Idempotency: if we already have strict gate in the approved-none block, do nothing.
    if 'SV_STRICT_EXPORTS' in s and "Skipping export." in s:
        print(f"OK: already patched: {path}")
        return False

    if NEEDLE_LINE not in s:
        raise SystemExit(f"ERROR: needle line not found in {path}")

    # Verify the structure is as expected: needle line followed soon by `return 2`
    idx = s.find(NEEDLE_LINE)
    window = s[idx:idx + 300]
    if RETURN_LINE not in window:
        raise SystemExit(f"ERROR: expected '{RETURN_LINE}' near needle in {path}; refusing.")

    # Replace only the first occurrence of NEEDLE_LINE + the first subsequent return 2
    s2 = ensure_import_os(s)

    # Recompute idx after possible import insertion
    idx2 = s2.find(NEEDLE_LINE)
    if idx2 == -1:
        raise SystemExit(f"ERROR: needle line disappeared after import rewrite in {path} (unexpected).")

    # Find the first "return 2" after the needle
    rpos = s2.find(RETURN_LINE, idx2)
    if rpos == -1:
        raise SystemExit(f"ERROR: could not find return 2 after needle in {path} (unexpected).")

    # Replace the needle line with the replacement block, then delete the original return 2
    out = s2.replace(NEEDLE_LINE, REPLACEMENT_BLOCK.rstrip("\n"), 1)

    # Remove exactly one `return 2` that belonged to the original block (first after the replaced message)
    # We do this by locating again after replacement.
    nidx = out.find("Skipping export.", idx2)
    if nidx == -1:
        # Should not happen; still safe to proceed without removing return 2? No: refuse.
        raise SystemExit(f"ERROR: failed to locate inserted block in {path}; refusing.")
    rpos2 = out.find(RETURN_LINE, nidx)
    if rpos2 == -1:
        raise SystemExit(f"ERROR: expected to find original return 2 after inserted block in {path}; refusing.")
    # Remove that one line (preserve newline)
    # Identify line bounds
    line_start = out.rfind("\n", 0, rpos2) + 1
    line_end = out.find("\n", rpos2)
    if line_end == -1:
        # EOF line
        out2 = out[:line_start]
    else:
        out2 = out[:line_start] + out[line_end+1:]

    if out2 == s:
        raise SystemExit(f"ERROR: patch produced no changes for {path} (unexpected).")

    path.write_text(out2, encoding="utf-8")
    print(f"OK: patched {path}")
    return True

def main() -> None:
    changed_any = False
    for p in TARGETS:
        changed_any = patch_one(p) or changed_any
    if not changed_any:
        print("OK: no changes needed.")

if __name__ == "__main__":
    main()
