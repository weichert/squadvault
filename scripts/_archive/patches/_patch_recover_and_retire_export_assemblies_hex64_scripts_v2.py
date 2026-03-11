from __future__ import annotations

import subprocess
from pathlib import Path

TARGET_DIR = Path("scripts/_retired/export_assemblies_hex64")
MARKER = "SV_PATCH_RECOVER_AND_RETIRE_EXPORT_ASSEMBLIES_HEX64_SCRIPTS_V2"

FILES = [
    "scripts/_patch_export_assemblies_define_hex64_re_v4.py",
    "scripts/patch_export_assemblies_define_hex64_re_v4.sh",
    "scripts/_patch_export_assemblies_define_hex64_re_local_v5.py",
    "scripts/patch_export_assemblies_define_hex64_re_local_v5.sh",
    "scripts/_patch_export_assemblies_remove_hex64_re_v4_artifact_v6.py",
    "scripts/patch_export_assemblies_remove_hex64_re_v4_artifact_v6.sh",
]


def sh(*args: str) -> str:
    proc = subprocess.run(list(args), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(args)}\nstderr:\n{proc.stderr}")
    return (proc.stdout or "").rstrip("\n")


def last_commit_where_file_exists(path: str) -> str | None:
    # Find last commit where file was Added or Modified (not Deleted).
    # This avoids selecting the deletion commit.
    try:
        out = sh("git", "log", "--format=%H", "--diff-filter=AM", "-n", "1", "--", path).strip()
        return out or None
    except Exception:
        return None


def git_show(commit: str, path: str) -> str:
    return sh("git", "show", f"{commit}:{path}")


def ensure_readme() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    readme = TARGET_DIR / "README.md"
    if readme.exists():
        # Stamp marker if missing (idempotent)
        s = readme.read_text(encoding="utf-8")
        if MARKER in s:
            return
        readme.write_text(s.rstrip() + f"\n\n<!-- {MARKER} -->\n", encoding="utf-8")
        return

    readme.write_text(
        "\n".join(
            [
                "# Retired: export-assemblies HEX64 patch scripts",
                "",
                "These scripts were created during iterative fixes to `export-assemblies` fingerprint validation,",
                "then superseded by newer canonical patches. They are retained here for auditability / archaeology.",
                "",
                "Do not re-enable these without a deliberate review.",
                "",
                f"<!-- {MARKER} -->",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    ensure_readme()

    recovered = 0
    skipped = 0

    for f in FILES:
        commit = last_commit_where_file_exists(f)
        if not commit:
            print(f"WARN: could not find any AM commit for {f}; skipping")
            skipped += 1
            continue

        try:
            blob = git_show(commit, f)
        except Exception as e:
            print(f"WARN: could not git-show {f} at {commit}; skipping ({e})")
            skipped += 1
            continue

        out_path = TARGET_DIR / Path(f).name
        if out_path.exists():
            # If already present, don't overwrite (idempotent)
            recovered += 1
            continue

        out_path.write_text(blob + ("\n" if not blob.endswith("\n") else ""), encoding="utf-8")
        recovered += 1

    print(f"OK: recovered/copied scripts into {TARGET_DIR} (recovered={recovered}, skipped={skipped}).")


if __name__ == "__main__":
    main()
