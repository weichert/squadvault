from __future__ import annotations

from pathlib import Path

MARKER = "SV_PATCH_CLEANUP_EXPORT_ASSEMBLIES_HEX64_PATCH_SCRIPTS_V1"

# Obsolete, superseded by v7 ("define HEX64_RE at top of main")
OBSOLETE = [
    Path("scripts/_patch_export_assemblies_define_hex64_re_v4.py"),
    Path("scripts/patch_export_assemblies_define_hex64_re_v4.sh"),
    Path("scripts/_patch_export_assemblies_define_hex64_re_local_v5.py"),
    Path("scripts/patch_export_assemblies_define_hex64_re_local_v5.sh"),
    Path("scripts/_patch_export_assemblies_remove_hex64_re_v4_artifact_v6.py"),
    Path("scripts/patch_export_assemblies_remove_hex64_re_v4_artifact_v6.sh"),
]

STAMP = Path("docs/80_indices/ops/_patch_stamps/cleanup_export_assemblies_hex64_patch_scripts_v1.stamp")


def main() -> None:
    STAMP.parent.mkdir(parents=True, exist_ok=True)

    removed: list[str] = []
    missing: list[str] = []

    for p in OBSOLETE:
        if p.exists():
            p.unlink()
            removed.append(str(p))
        else:
            missing.append(str(p))

    STAMP.write_text(
        "\n".join(
            [
                f"{MARKER}",
                "removed:",
                *[f"- {x}" for x in removed],
                "missing (already gone):",
                *[f"- {x}" for x in missing],
                "",
            ]
        ),
        encoding="utf-8",
    )

    if removed:
        print("OK: removed obsolete HEX64 patch scripts:")
        for x in removed:
            print(f"  - {x}")
    else:
        print("OK: no obsolete HEX64 patch scripts found (already removed).")

    print(f"OK: stamped {STAMP}")


if __name__ == "__main__":
    main()
