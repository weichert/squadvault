from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
MARKER = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

# Replace a standalone 'continue' within the marker block with 'return 0'
CONTINUE_RE = re.compile(r"^(\s*)continue\s*$")


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    p = _root() / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)
    lines = s.splitlines(keepends=True)

    out: list[str] = []
    changed = False

    in_block = False
    block_seen = False
    # We only rewrite the first marker block we find.
    for ln in lines:
        if ln.rstrip("\n") == MARKER:
            in_block = True
            block_seen = True
            out.append(ln)
            continue

        if in_block:
            # End marker block conservatively at 'fi'
            if ln.strip() == "fi":
                in_block = False
                out.append(ln)
                continue

            m = CONTINUE_RE.match(ln.rstrip("\n"))
            if m:
                indent = m.group(1)
                out.append(f"{indent}return 0\n")
                changed = True
                continue

        out.append(ln)

    if not block_seen:
        raise SystemExit(
            f"ERROR: marker block not found: {MARKER}\n"
            "Expected v9 to have inserted it. Refusing to guess placement."
        )

    new_s = "".join(out)
    if new_s == s:
        _chmod_x(p)
        print("OK: pytest array-expansion guard already uses return (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    print("OK: updated pytest array-expansion guard to return 0 (v10).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
