from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)


def _git_ls_files(root: Path, pattern: str) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", pattern],
        cwd=str(root),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout
    return [root / line.strip() for line in out.splitlines() if line.strip()]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, text: str) -> bool:
    if p.exists() and _read(p) == text:
        return False
    p.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    root = _repo_root()
    scripts = _git_ls_files(root, "scripts/*.sh")

    total_hits = 0
    changed_files: list[str] = []

    for path in scripts:
        s = _read(path)
        lines = s.splitlines(True)
        hit = 0

        for i, line in enumerate(lines):
            # Match: optional whitespace then '==>' at start of content.
            stripped = line.lstrip()
            if stripped.startswith("==>"):
                # Convert bare marker into echo "..."
                raw = line.rstrip("\n")
                indent = raw[: len(raw) - len(raw.lstrip())]
                marker = raw.strip()
                lines[i] = f'{indent}echo "{marker}"\n'
                hit += 1

        if hit:
            total_hits += hit
            new_s = "".join(lines)
            if _write_if_changed(path, new_s):
                changed_files.append(str(path.relative_to(root)))

    if total_hits == 0:
        print("OK: no bare '==>' marker lines found in tracked scripts/*.sh (nothing to do).")
        return 0

    print(f"OK: converted {total_hits} bare '==>' marker line(s) across {len(changed_files)} file(s).")
    for f in changed_files:
        print(f" - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
