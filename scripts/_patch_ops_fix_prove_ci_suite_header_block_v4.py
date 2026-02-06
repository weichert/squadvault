from __future__ import annotations

from pathlib import Path
import subprocess
import sys


TARGET = Path("scripts/prove_ci.sh")


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, text: str) -> bool:
    if p.exists() and _read(p) == text:
        return False
    p.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    root = _repo_root()
    path = root / TARGET
    if not path.exists():
        print(f"FATAL: missing {TARGET}", file=sys.stderr)
        return 2

    s = _read(path)
    lines = s.splitlines(True)

    # Find the canonical suite header block start.
    # We key off the exact suite header line you now have.
    start = None
    for i, line in enumerate(lines):
        if line.strip() == 'echo "== CI Proof Suite =="':
            start = i
            break

    if start is None:
        print('FATAL: could not find: echo "== CI Proof Suite =="', file=sys.stderr)
        return 3

    # Ensure the next ~10 lines include the pairing gate call; otherwise, fail closed.
    window = "".join(lines[start : min(len(lines), start + 20)])
    if "bash scripts/check_patch_pairs_v1.sh" not in window:
        print("FATAL: suite header found but pairing gate call not nearby; refusing to patch.", file=sys.stderr)
        print("HINT: show context with:", file=sys.stderr)
        print("  nl -ba scripts/prove_ci.sh | sed -n '115,160p'", file=sys.stderr)
        return 4

    # Remove a single dangling-quote line immediately following the pairing gate call block.
    removed = 0
    for j in range(start, min(len(lines) - 1, start + 25)):
        if lines[j].strip() == "bash scripts/check_patch_pairs_v1.sh":
            # Skip any blank lines after the call, then check for a lone quote.
            k = j + 1
            while k < len(lines) and lines[k].strip() == "":
                k += 1
            if k < len(lines) and lines[k].strip() == '"':
                del lines[k]
                removed = 1
            break

    if removed != 1:
        print('FATAL: did not find a removable dangling quote line after pairing gate call.', file=sys.stderr)
        print("HINT: show context with:", file=sys.stderr)
        print("  nl -ba scripts/prove_ci.sh | sed -n '115,160p'", file=sys.stderr)
        return 5

    out = "".join(lines)
    changed = _write_if_changed(path, out)
    print("OK: patch applied (v4) — removed dangling quote." if changed else "OK: no changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
