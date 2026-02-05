from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")
MARKER = "SV_PATCH_EXPORT_ASSEMBLIES_REMOVE_HEX64_RE_V4_ARTIFACT_V6"

V4_MARK = "# SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_V4"
HEX64_LINE = 'HEX64_RE = re.compile(r"^[0-9a-f]{64}$")'


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    out: list[str] = []
    removed_v4 = 0
    removed_hex = 0

    for line in lines:
        # Remove the misplaced v4 marker
        if line.rstrip("\n") == V4_MARK:
            removed_v4 += 1
            continue

        # Remove the orphaned HEX64_RE assignment line (any indentation),
        # but DO NOT touch the v5 local marker line.
        if line.strip("\n").strip() == HEX64_LINE:
            removed_hex += 1
            continue

        out.append(line)

    if removed_v4 == 0 and removed_hex == 0:
        # Still stamp marker so the patch is auditable + idempotent.
        # Insert it near the top (after imports) as a no-op marker.
        # Heuristic: after last import/from line.
        insert_i = 0
        for i, line in enumerate(out):
            st = line.lstrip()
            if st.startswith("import ") or st.startswith("from "):
                insert_i = i + 1
        out.insert(insert_i, f"\n# {MARKER}\n")
        TARGET.write_text("".join(out), encoding="utf-8")
        print(f"OK: {TARGET} had no v4 artifact lines; stamped marker ({MARKER}).")
        return

    # Stamp marker right where the v4 marker used to be if possible; otherwise after imports.
    insert_i = 0
    for i, line in enumerate(out):
        st = line.lstrip()
        if st.startswith("import ") or st.startswith("from "):
            insert_i = i + 1
    out.insert(insert_i, f"\n# {MARKER}\n")

    TARGET.write_text("".join(out), encoding="utf-8")
    print(
        f"OK: patched {TARGET} (removed v4 marker lines: {removed_v4}; "
        f"removed orphan HEX64_RE lines: {removed_hex})."
    )


if __name__ == "__main__":
    main()
