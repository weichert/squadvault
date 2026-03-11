from __future__ import annotations

import subprocess
from pathlib import Path

ARCHIVE_DIR = Path("scripts/_retired")

# These paths were deleted in the retire commit; their last-good contents are in HEAD~1.
SOURCES = [
    "scripts/_patch_add_prove_local_clean_then_ci_v1.py",
    "scripts/_patch_add_prove_local_clean_then_ci_v2.py",
    "scripts/patch_add_prove_local_clean_then_ci_v1.sh",
    "scripts/patch_add_prove_local_clean_then_ci_v2.sh",
    "scripts/prove_local_clean_then_ci_v1.sh",
    "scripts/prove_local_clean_then_ci_v2.sh",
]


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def git_show(rev_path: str) -> str:
    # rev_path like "HEAD~1:scripts/foo.sh"
    r = subprocess.run(
        ["git", "show", rev_path],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if r.returncode != 0:
        die(f"git show failed for {rev_path}: {r.stderr.strip()}")
    return r.stdout


def write_refuse_on_diff(path: Path, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return
        die(f"refusing to modify existing archive file with unexpected contents: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for src in SOURCES:
        content = git_show(f"HEAD~1:{src}")
        dest = ARCHIVE_DIR / Path(src).name
        write_refuse_on_diff(dest, content)
        written += 1

    print(f"OK: archived {written} retired files under {ARCHIVE_DIR}/ (sourced from HEAD~1)")


if __name__ == "__main__":
    main()
