from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")
MARKER = "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_IN_MAIN_V7"

V5_MARK = "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_LOCAL_V5"
HEX64_LINE = 'HEX64_RE = re.compile(r"^[0-9a-f]{64}$")'


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    # 1) Ensure import re exists at module scope.
    if not any(l.strip() == "import re" for l in lines):
        last_import_i = None
        for i, line in enumerate(lines):
            st = line.lstrip()
            if st.startswith("import ") or st.startswith("from "):
                last_import_i = i
        if last_import_i is None:
            raise SystemExit(f"ERROR: could not find imports block in {TARGET}")
        lines.insert(last_import_i + 1, "import re\n")

    # 2) Remove any previous HEX64_RE compile lines (any indent) + the old v5 marker line.
    cleaned: list[str] = []
    removed_hex = 0
    removed_v5 = 0

    for line in lines:
        if V5_MARK in line:
            removed_v5 += 1
            continue
        if line.strip() == HEX64_LINE:
            removed_hex += 1
            continue
        cleaned.append(line)

    lines = cleaned

    # 3) Insert a definitive local HEX64_RE right after `def main(...):`
    def_i = None
    for i, line in enumerate(lines):
        if line.startswith("def main("):
            def_i = i
            break
    if def_i is None:
        raise SystemExit("ERROR: could not find 'def main(' in target")

    # Insert after the function signature line.
    # Determine indent for function body = 4 spaces (project style)
    insert_at = def_i + 1
    snippet = (
        f"    # {MARKER}\n"
        f"    HEX64_RE = re.compile(r\"^[0-9a-f]{{64}}$\")\n"
        "\n"
    )
    lines.insert(insert_at, snippet)

    TARGET.write_text("".join(lines), encoding="utf-8")
    print(
        f"OK: patched {TARGET} (removed old HEX64_RE lines={removed_hex}; "
        f"removed v5 marker lines={removed_v5}; inserted HEX64_RE inside main)."
    )


if __name__ == "__main__":
    main()
