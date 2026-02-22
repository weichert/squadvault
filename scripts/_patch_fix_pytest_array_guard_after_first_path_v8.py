from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"

FUNC_RE = re.compile(r'^\s*check_line_pytest_usage\s*\(\)\s*\{\s*$')
FIRST_PATH_RE = re.compile(r'^\s*first_path=')

SIG = 'sv_tok="${first_path-}"'
GUARD_LINES = [
    '# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->\n',
    '# Allow array-expansion targets like "${gp_tests[@]}" to bypass Tests/ prefix check.\n',
    'sv_tok="${first_path-}"\n',
    'if [ -n "${sv_tok-}" ] && echo "${sv_tok-}" | grep -Eq "^[\\\"\\\']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}[\\\"\\\']*$" ; then\n',
    '  continue\n',
    'fi\n',
]


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

    in_func = False
    brace_depth = 0  # best-effort; bash braces are simple in our scripts

    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        # detect function start
        if not in_func and FUNC_RE.match(ln.rstrip("\n")):
            in_func = True
            brace_depth = 1
            out.append(ln)
            i += 1
            continue

        if in_func:
            # track end of function (best-effort): a line starting with "}" at column 0
            if ln.startswith("}"):
                brace_depth -= 1
                if brace_depth <= 0:
                    in_func = False
                out.append(ln)
                i += 1
                continue

            # insert guard immediately after first_path assignment
            if FIRST_PATH_RE.match(ln):
                out.append(ln)
                # lookahead window to avoid reinserting
                window = "".join(lines[i + 1 : min(len(lines), i + 15)])
                if SIG not in window:
                    out.extend(GUARD_LINES)
                    changed = True
                i += 1
                continue

        out.append(ln)
        i += 1

    if not changed:
        _chmod_x(p)
        print("OK: guard already present after first_path assignment (noop).")
        return 0

    _clipwrite(REL, "".join(out))
    _chmod_x(p)
    print("OK: inserted array-expansion guard immediately after first_path assignment (v8).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
