from __future__ import annotations

from pathlib import Path
import os
import subprocess


ALLOWLIST = Path("scripts/patch_pair_allowlist_v1.txt")
PREFIX = "ALLOWLISTED: missing pair for "


HEADER = """# patch_pair_allowlist_v1.txt
# Canonical allowlist for legacy patcher/wrapper pairing exceptions.
#
# Rule:
#   - New unpaired patchers/wrappers MUST NOT be added.
#   - If an exception is truly required, add it here (reviewable).
#
# One path per line, exact match, git-tracked only.
"""


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(out)


def current_allowlisted_missing_pairs(root: Path) -> list[str]:
    env = dict(os.environ)
    env["SV_PATCH_PAIR_VERBOSE"] = "1"

    p = subprocess.run(
        ["bash", "scripts/check_patch_pairs_v1.sh"],
        cwd=str(root),
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    paths: list[str] = []
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            paths.append(line[len(PREFIX):].strip())

    # Deterministic output
    return sorted(set(paths))


def main() -> int:
    root = repo_root()
    os.chdir(root)

    paths = current_allowlisted_missing_pairs(root)

    out = HEADER
    if paths:
        out += "\n" + "\n".join(paths) + "\n"
    else:
        out += "\n"

    ALLOWLIST.write_text(out, encoding="utf-8")
    print(f"OK: rewrote {ALLOWLIST} (entries={len(paths)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
