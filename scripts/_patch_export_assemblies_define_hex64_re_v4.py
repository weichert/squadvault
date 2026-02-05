from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")

MARKER = "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_V4"


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    # 1) Ensure `import re` exists (near the other imports).
    has_import_re = any(l.strip() == "import re" for l in lines)

    # Find an insertion point: after the last contiguous import line.
    # Heuristic: insert after the last line that starts with "import " or "from ".
    last_import_i = None
    for i, line in enumerate(lines):
        st = line.lstrip()
        if st.startswith("import ") or st.startswith("from "):
            last_import_i = i

    if last_import_i is None:
        raise SystemExit(f"ERROR: could not find imports block in {TARGET}")

    if not has_import_re:
        lines.insert(last_import_i + 1, "import re\n")
        last_import_i += 1  # shift insertion point

    # 2) Define HEX64_RE if missing.
    if "HEX64_RE" not in s:
        # Insert near other module-level constants.
        insert_i = last_import_i + 1
        snippet = (
            "\n"
            f"# {MARKER}\n"
            "HEX64_RE = re.compile(r\"^[0-9a-f]{64}$\")\n"
        )
        lines.insert(insert_i, snippet)
    else:
        # If HEX64_RE exists but marker doesn't, still add marker comment nearby to make idempotent.
        # We’ll place the marker comment near the first occurrence.
        for i, line in enumerate(lines):
            if "HEX64_RE" in line:
                lines.insert(i, f"# {MARKER}\n")
                break

    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"OK: patched {TARGET} (define HEX64_RE; ensure import re).")


if __name__ == "__main__":
    main()
