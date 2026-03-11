from __future__ import annotations

from pathlib import Path
from datetime import datetime

REPO = Path(".")
SCRIPTS = REPO / "scripts"
RETIRED = SCRIPTS / "_retired"
MARKER = "SV_PATCH_CLEANUP_EXPORT_ASSEMBLIES_HEX64_PATCH_SCRIPTS_V1"

# We only retire scripts that are clearly superseded by the v7 final approach:
#   - HEX64_RE defined at top of main
# and/or that were explicit intermediate fixes.
RETIRE_CANDIDATES = [
    # v4: attempted module-level define; ended up as a stray artifact later
    "patch_export_assemblies_define_hex64_re_v4.sh",
    "_patch_export_assemblies_define_hex64_re_v4.py",

    # v5: local insertion right above the `if HEX64_RE.match...` line (intermediate)
    "patch_export_assemblies_define_hex64_re_local_v5.sh",
    "_patch_export_assemblies_define_hex64_re_local_v5.py",

    # v6: removed stray artifact from v4 (intermediate cleanup)
    "patch_export_assemblies_remove_hex64_re_v4_artifact_v6.sh",
    "_patch_export_assemblies_remove_hex64_re_v4_artifact_v6.py",
]


def _stamp_retired_readme() -> None:
    RETIRED.mkdir(parents=True, exist_ok=True)
    readme = RETIRED / "README.md"
    if readme.exists():
        return
    readme.write_text(
        "# Retired patch scripts\n\n"
        f"- Marker: `{MARKER}`\n"
        "- These patch scripts were retained for auditability but are **superseded** by the\n"
        "  canonical v7 approach (define `HEX64_RE` at top of export-assemblies `main`).\n"
        "- They are moved here to reduce operator confusion and avoid re-running obsolete steps.\n",
        encoding="utf-8",
    )


def _move(rel: str) -> tuple[bool, str]:
    src = SCRIPTS / rel
    if not src.exists():
        return (False, f"SKIP: missing {src}")
    dst = RETIRED / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dst)
    return (True, f"MOVED: {src} -> {dst}")


def main() -> None:
    # Idempotency marker: if README exists, and none of candidates exist in scripts/,
    # we consider it already applied.
    already = True
    for rel in RETIRE_CANDIDATES:
        if (SCRIPTS / rel).exists():
            already = False
            break
    if already and (RETIRED / "README.md").exists():
        print(f"OK: cleanup already applied ({MARKER}).")
        return

    _stamp_retired_readme()

    moved_any = False
    for rel in RETIRE_CANDIDATES:
        moved, msg = _move(rel)
        print(msg)
        moved_any = moved_any or moved

    # Add a small stamp file so future audits have a crisp “this ran” artifact.
    stamp = RETIRED / f"{MARKER}.txt"
    if not stamp.exists():
        stamp.write_text(
            f"{MARKER}\n"
            f"applied_utc={datetime.utcnow().isoformat(timespec='seconds')}Z\n",
            encoding="utf-8",
        )

    if not moved_any:
        print("NOTE: no candidate scripts were present to retire (nothing moved).")
    print("OK: cleanup complete.")


if __name__ == "__main__":
    main()
