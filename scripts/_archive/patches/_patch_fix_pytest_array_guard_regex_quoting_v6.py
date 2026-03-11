from __future__ import annotations

from pathlib import Path
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
MARKER = "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1"


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


CANON_BLOCK = [
    'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"\n',
    # NOTE: double-quoted regex; simple + unambiguous.
    'if [ -n "${sv_tok-}" ] && echo "${sv_tok-}" | grep -Eq "^[\\\"\\\']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}[\\\"\\\']*$" ; then\n',
    "  continue\n",
    "fi\n",
]


def _is_canon(window: str) -> bool:
    return (
        'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"' in window
        and 'grep -Eq "^[\\\"\\\']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}[\\\"\\\']*$"' in window
        and "  continue\n" in window
    )


def main() -> int:
    p = _root() / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)
    if MARKER not in s:
        raise SystemExit(f"ERROR: marker {MARKER} not found in {REL} (refusing).")

    lines = s.splitlines(keepends=True)
    out: list[str] = []
    changed = False
    i = 0

    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        i += 1

        if MARKER not in ln:
            continue

        # After marker, keep comment lines (starting with '#') as-is
        while i < len(lines) and lines[i].lstrip().startswith("#") and MARKER not in lines[i]:
            out.append(lines[i])
            i += 1

        # Now rewrite the following guard body up through the closing fi (inclusive).
        # We scan forward to the first 'fi' and replace that whole region.
        j = i
        fi_idx = None
        while j < len(lines):
            if lines[j].lstrip().startswith("fi"):
                fi_idx = j
                break
            j += 1

        if fi_idx is None:
            raise SystemExit(f"ERROR: marker found but no closing 'fi' found in {REL} (refusing).")

        existing = "".join(lines[i : fi_idx + 1])
        if _is_canon(existing):
            # Keep existing as-is
            out.extend(lines[i : fi_idx + 1])
        else:
            out.extend(CANON_BLOCK)
            changed = True

        i = fi_idx + 1

    if not changed:
        _chmod_x(p)
        print("OK: guard blocks already canonical (noop).")
        return 0

    _clipwrite(REL, "".join(out))
    _chmod_x(p)
    print("OK: rewrote SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 guard blocks with unambiguous regex quoting (v6).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
