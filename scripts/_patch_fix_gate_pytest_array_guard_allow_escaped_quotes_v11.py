from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
MARKER = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

# We rewrite only the grep -Eq line within the marker block.
# Old:  grep -Eq "^[\"']*\$\{...}[\"']*$"
# New:  grep -Eq "^[\\\"\\']*\$\{...}[\\\"\\']*$"   (adds backslash as allowed wrapper)
GREP_LINE_OLD_RE = re.compile(r'^\s*if \[ -n "\$\{sv_tok-\}" \ ] && echo "\$\{sv_tok-\}" \| grep -Eq ".*_tests\\\[@\\\]\\\}.*"\s*;\s*then\s*$')
GREP_EQ_RE = re.compile(r'^\s*if \[ -n "\$\{sv_tok-\}" \ ] && echo "\$\{sv_tok-\}" \| grep -Eq "(?P<re>[^"]+)"\s*;\s*then\s*$')

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
    grep_line_seen = False

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

            m = GREP_EQ_RE.match(ln.rstrip("\n"))
            if m:
                grep_line_seen = True
                old_re = m.group("re")
                # If already includes backslash in wrapper char class, noop.
                if "[\\\\\\\"\\\\\\']" in old_re or "[\\\\\"\\\\']" in old_re:
                    out.append(ln)
                    continue

                # Replace leading/trailing wrapper classes [\"'] with [\\\"\\']
                new_re = old_re
                new_re = new_re.replace('^[\\"\\\']*', '^[\\\\\\"\\\\\']*')
                new_re = new_re.replace('[\\"\\\']*$', '[\\\\\\"\\\\\']*$')

                # If the above didn't hit (different escaping), do a conservative rewrite
                # to the canonical intended pattern.
                if new_re == old_re:
                    new_re = r'^[\\\"\\\']*\$\{[A-Za-z0-9_]+_tests\[@\]\}[\\\"\\\']*$'

                out.append(re.sub(r'"[^"]+"', f'"{new_re}"', ln, count=1))
                changed = True
                continue

        out.append(ln)

    if not block_seen:
        raise SystemExit(f"ERROR: marker block not found: {MARKER}")

    if not grep_line_seen:
        raise SystemExit("ERROR: did not find grep -Eq line within marker block to rewrite.")

    new_s = "".join(out)
    if new_s == s:
        _chmod_x(p)
        print("OK: pytest array-expansion guard already allows escaped quotes (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    print("OK: widened pytest array-expansion guard to allow escaped quotes (v11).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
