from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")
MARKER = "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_LOCAL_V5"

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    # Ensure import re exists somewhere at top-level.
    if not any(l.strip() == "import re" for l in lines):
        # Insert after last import/from line.
        last_import_i = None
        for i, line in enumerate(lines):
            st = line.lstrip()
            if st.startswith("import ") or st.startswith("from "):
                last_import_i = i
        if last_import_i is None:
            raise SystemExit(f"ERROR: could not find imports block in {TARGET}")
        lines.insert(last_import_i + 1, "import re\n")

    # Find the first occurrence of `if HEX64_RE.match(_approved_fp):`
    needle = "if HEX64_RE.match(_approved_fp):"
    hit = None
    for i, line in enumerate(lines):
        if needle in line:
            hit = i
            break
    if hit is None:
        raise SystemExit(f"ERROR: could not find '{needle}' in {TARGET}")

    # Determine indentation of the `if` line and insert local def right above it.
    indent = lines[hit].split("if", 1)[0]
    insert = (
        f"{indent}# {MARKER}\n"
        f"{indent}HEX64_RE = re.compile(r\"^[0-9a-f]{{64}}$\")\n"
    )
    lines.insert(hit, insert)

    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"OK: patched {TARGET} (define HEX64_RE locally inside main).")

if __name__ == "__main__":
    main()
