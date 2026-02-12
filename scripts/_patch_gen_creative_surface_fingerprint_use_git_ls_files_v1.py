from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


TARGET = Path("scripts/gen_creative_surface_fingerprint_v1.py")


CANONICAL = """\
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


OUT = Path("artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json")
ROOTS = [
    "artifacts/exports",
    "artifacts/creative",
]
VERSION = 1


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return Path(p.stdout.strip())


def _git_ls_files(paths: list[str]) -> list[str]:
    # Deterministic: git already emits sorted-ish output, but we sort anyway.
    p = subprocess.run(
        ["git", "ls-files", "--"] + paths,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    return sorted(out)


def _sha256_bytes(p: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with p.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
            n += len(b)
    return (h.hexdigest(), n)


def main() -> None:
    repo = _repo_root()
    paths = _git_ls_files(ROOTS)

    files: list[dict[str, object]] = []
    for rel in paths:
        fp = repo / rel
        # ls-files should only return tracked existing files, but be defensive.
        if not fp.is_file():
            continue
        sha, n = _sha256_bytes(fp)
        files.append(
            {
                "bytes": int(n),
                "path": rel,
                "sha256": sha,
            }
        )

    payload = {
        "file_count": len(files),
        "files": files,
        "roots": list(ROOTS),
        "version": VERSION,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\\n", encoding="utf-8")
    print(f"OK: wrote {OUT} (files={len(files)})")


if __name__ == "__main__":
    main()
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    cur = TARGET.read_text(encoding="utf-8")
    if cur == CANONICAL:
        print("OK: gen_creative_surface_fingerprint_v1.py already canonical (noop)")
        return

    # NOTE: newline must be a real newline value (e.g. "\n"), not "\\n".
    TARGET.write_text(CANONICAL, encoding="utf-8", newline="\n")
    print("OK: updated gen_creative_surface_fingerprint_v1.py (git ls-files mode)")


if __name__ == "__main__":
    main()
