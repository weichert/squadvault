from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess

REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
MARKER = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

# Canonical regex to allow optional wrappers consisting of ", ', or backslash-escaped quotes.
NEW_RE = r'^[\\\"\\\']*\$\{[A-Za-z0-9_]+_tests\[@\]\}[\\\"\\\']*$'

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
    rewritten = False

    for ln in lines:
        if ln.rstrip("\n") == MARKER:
            in_block = True
            block_seen = True
            out.append(ln)
            continue

        if in_block:
            if ln.strip() == "fi":
                in_block = False
                out.append(ln)
                continue

            # Find the grep -Eq "..." line inside the marker block and rewrite the quoted regex payload.
            if (not rewritten) and ("grep -Eq " in ln) and ('grep -Eq "' in ln):
                # If already updated, noop.
                if NEW_RE in ln:
                    out.append(ln)
                    rewritten = True
                    continue

                # Replace the first quoted string after grep -Eq with NEW_RE.
                # Keep any indentation / suffix intact.
                m = re.search(r'(grep -Eq ")([^"]*)(")', ln)
                if not m:
                    raise SystemExit("ERROR: found grep -Eq line but could not parse quoted regex payload.")

                prefix = ln[: m.start(2)]
                suffix = ln[m.end(2) :]
                out.append(prefix + NEW_RE + suffix)
                changed = True
                rewritten = True
                continue

        out.append(ln)

    if not block_seen:
        raise SystemExit(f"ERROR: marker block not found: {MARKER}")

    if not rewritten:
        raise SystemExit('ERROR: did not find a grep -Eq "..." line inside the marker block to rewrite.')

    new_s = "".join(out)
    if new_s == s:
        _chmod_x(p)
        print("OK: guard regex already allows escaped quotes (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    print("OK: widened guard regex to allow escaped quotes (v12).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
