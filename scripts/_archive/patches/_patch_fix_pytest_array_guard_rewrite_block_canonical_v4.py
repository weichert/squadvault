from __future__ import annotations

from pathlib import Path
import stat
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
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


MARKER_LINE = "# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->"

# Canonical guard block (set -u safe + quote-tolerant + variable-agnostic):
# Accepts: ${gp_tests[@]}, "${gp_tests[@]}", '${gp_tests[@]}', '"${gp_tests[@]}"'
CANON_GUARD_LINES = [
    'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"\n',
    "if [ -n \"${sv_tok-}\" ] && echo \"${sv_tok-}\" | "
    "grep -Eq '^['\"'\"']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}['\"'\"']*$' ; then\n",
    "  continue\n",
    "fi\n",
]


def _is_canonical_window(lines: list[str]) -> bool:
    blob = "".join(lines)
    return (
        'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"' in blob
        and "grep -Eq '^['\"'\"']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}['\"'\"']*$'" in blob
        and "\n  continue\n" in blob
    )


def _rewrite_marker_block(rel: str) -> bool:
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)
    lines = s.splitlines(keepends=True)

    if MARKER_LINE not in s:
        _chmod_x(p)
        print(f"OK: {rel} has no marker; nothing to rewrite (noop).")
        return False

    out: list[str] = []
    changed = False
    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln.rstrip("\n") == MARKER_LINE:
            # Copy marker line
            out.append(ln)
            i += 1

            # Copy subsequent comment lines (starting with "#") immediately under the marker
            comment_start = i
            while i < len(lines) and lines[i].lstrip().startswith("#") and "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1" not in lines[i]:
                out.append(lines[i])
                i += 1

            # Now we expect the old guard body (sv_tok/if/continue/fi).
            # Skip everything until (and including) the first "fi" that closes this guard.
            guard_start = i
            fi_idx = None
            j = i
            while j < len(lines):
                if lines[j].lstrip().startswith("fi"):
                    fi_idx = j
                    break
                j += 1

            if fi_idx is None:
                raise SystemExit(f"ERROR: marker found but no closing 'fi' found in {rel} (refusing).")

            # If the existing block is already canonical, keep it as-is.
            existing_block = lines[guard_start : fi_idx + 1]
            if _is_canonical_window(existing_block):
                out.extend(existing_block)
                i = fi_idx + 1
                continue

            # Otherwise, replace with canonical guard.
            out.extend(CANON_GUARD_LINES)
            i = fi_idx + 1
            changed = True
            continue

        out.append(ln)
        i += 1

    if not changed:
        _chmod_x(p)
        print(f"OK: {rel} already canonical (noop).")
        return False

    _clipwrite(rel, "".join(out))
    _chmod_x(p)
    print(f"OK: rewrote marker guard block(s) canonically in {rel} (v4).")
    return True


def main() -> int:
    changed = _rewrite_marker_block("scripts/gate_pytest_tracked_tests_only_v1.sh")
    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
