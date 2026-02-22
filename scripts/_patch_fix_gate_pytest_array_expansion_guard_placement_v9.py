from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"

# We will insert the guard immediately before the violation append line.
VIOL_RE = re.compile(r"^\s*violations\+\=.*pytest target must start with Tests/.*\n?$")

MARKER = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

GUARD_BLOCK = [
    f"{MARKER}\n",
    "# Allow array-expansion targets like \"${gp_tests[@]}\" (optionally quoted) to bypass Tests/ prefix check.\n",
    # Prefer first_path (the value used in the violation message), but fall back to earlier locals if present.
    'sv_tok="${first_path-${t-${tok-${arg-${target-${raw-}}}}}}"\n',
    'if [ -n "${sv_tok-}" ] && echo "${sv_tok-}" | grep -Eq "^[\\\"\\\']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}[\\\"\\\']*$" ; then\n',
    "  continue\n",
    "fi\n",
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


def _remove_existing_guard(lines: list[str]) -> tuple[list[str], bool]:
    """
    Remove any existing block that begins with the marker and ends at the next 'fi'
    (inclusive). This is conservative and avoids leaving a misplaced 'continue'.
    """
    out: list[str] = []
    changed = False

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.rstrip("\n") == MARKER:
            changed = True
            # skip until and including the next line that is exactly 'fi'
            i += 1
            while i < len(lines):
                if lines[i].strip() == "fi":
                    i += 1
                    break
                i += 1
            continue
        out.append(ln)
        i += 1

    return out, changed


def main() -> int:
    p = _root() / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)
    lines = s.splitlines(keepends=True)

    # 1) remove any existing guard block anywhere (misplaced prior attempts)
    lines2, removed = _remove_existing_guard(lines)

    # 2) insert guard immediately before the violation append line
    out: list[str] = []
    inserted = False

    for ln in lines2:
        if (not inserted) and VIOL_RE.match(ln):
            out.extend(GUARD_BLOCK)
            inserted = True
        out.append(ln)

    if not inserted:
        raise SystemExit(
            "ERROR: could not find violation append line to anchor insertion. "
            "Expected a line starting with 'violations+=' containing "
            "'pytest target must start with Tests/'."
        )

    new_s = "".join(out)

    # idempotence: if content identical, noop
    if new_s == s:
        _chmod_x(p)
        print("OK: pytest array-expansion guard already correctly placed (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    if removed:
        print("OK: relocated pytest array-expansion guard to decision point (v9); removed prior misplaced block(s).")
    else:
        print("OK: inserted pytest array-expansion guard at decision point (v9).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
