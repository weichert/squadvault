from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess

REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"

MARKER = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

# Anchor: the violation append line (we insert / replace guard immediately before it).
VIOL_RE = re.compile(r'^\s*violations\+\="\$\{file\}:\$\{lineno\}: pytest target must start with Tests/ \(found .*')

# Replace everything from MARKER through the first following "fi" (inclusive),
# BUT only when that block occurs before the violation append line.
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

GUARD_BLOCK = [
    f"{MARKER}\n",
    '# Allow array-expansion targets like "${gp_tests[@]}" to bypass Tests/ prefix check.\n',
    '# Also tolerate optional surrounding quotes: "${...}", \'${...}\', \\"${...}\\", \\\'${...}\\\'.\n',
    'sv_tok="${first_path-${t-${tok-${arg-${target-${raw-}}}}}}"\n',
    'sv_norm="${sv_tok-}"\n',
    'for _sv_i in 1 2 3 4; do\n',
    '  case "$sv_norm" in\n',
    '    \\\\\\"*\\\\\\") sv_norm="${sv_norm#\\\\\\"}"; sv_norm="${sv_norm%\\\\\\"}";;\n',
    "    \\\\\\'*\\\\\\') sv_norm=\"${sv_norm#\\\\\\'}\"; sv_norm=\"${sv_norm%\\\\\\'}\";;\n",
    '    \\"*\\")       sv_norm="${sv_norm#\\"}";   sv_norm="${sv_norm%\\"}";;\n',
    "    \\'*\\')       sv_norm=\"${sv_norm#\\'}\";   sv_norm=\"${sv_norm%\\'}\";;\n",
    '    *) break;;\n',
    '  esac\n',
    'done\n',
    'if [ -n "${sv_norm-}" ] && echo "${sv_norm-}" | grep -Eq "^\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}$" ; then\n',
    '  return 0\n',
    'fi\n',
]

def main() -> int:
    p = _root() / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)
    lines = s.splitlines(keepends=True)

    # Find marker block start
    try:
        m_idx = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == MARKER)
    except StopIteration:
        raise SystemExit(f"ERROR: marker not found: {MARKER}")

    # Find the violation line after marker (must exist)
    try:
        v_idx = next(i for i in range(m_idx, min(len(lines), m_idx + 80)) if VIOL_RE.match(lines[i]))
    except StopIteration:
        raise SystemExit("ERROR: could not find violation append line after marker (refusing to guess).")

    # Find end of current marker guard block: first line that is exactly 'fi' between marker and violation
    try:
        fi_idx = next(i for i in range(m_idx, v_idx) if lines[i].strip() == "fi")
    except StopIteration:
        raise SystemExit("ERROR: could not find end of marker block (fi) before violation line.")

    # Replace [m_idx .. fi_idx] inclusive with canonical GUARD_BLOCK
    new_lines = []
    new_lines.extend(lines[:m_idx])
    new_lines.extend(GUARD_BLOCK)
    new_lines.extend(lines[fi_idx + 1 :])

    new_s = "".join(new_lines)
    if new_s == s:
        _chmod_x(p)
        print("OK: pytest array-expansion guard already canonicalized (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    print("OK: rewrote pytest array-expansion guard to safe-normalize quotes (v13).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
