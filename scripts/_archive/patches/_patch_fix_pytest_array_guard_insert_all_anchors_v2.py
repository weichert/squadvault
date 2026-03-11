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


MARKER = "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1"
ANCHOR = "pytest target must start with Tests/"

GUARD = (
    '# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->\n'
    '# Accept pytest targets that are array expansions (already validated elsewhere).\n'
    '# Examples: "${gp_tests[@]}", ${gp_tests[@]}\n'
    'if [ -n "${t-}" ] && echo "${t-}" | grep -Eq \'^"?\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}"?$\' ; then\n'
    '  continue\n'
    'fi\n'
)


def _patch_gate_insert_all() -> bool:
    root = _repo_root()
    rel = "scripts/gate_pytest_tracked_tests_only_v1.sh"
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)
    if ANCHOR not in s:
        raise SystemExit(f"ERROR: anchor text not found in {rel} (refusing).")

    lines = s.splitlines(keepends=True)
    out: list[str] = []
    inserted_count = 0

    # Insert GUARD before *each* anchor line, unless a marker already appears very near above.
    for i, ln in enumerate(lines):
        if ANCHOR in ln:
            window = "".join(lines[max(0, i - 6) : i])
            if MARKER not in window:
                out.append(GUARD)
                inserted_count += 1
        out.append(ln)

    s2 = "".join(out)

    # Idempotence: if no new insertions, noop.
    if inserted_count == 0:
        _chmod_x(p)
        print("OK: gate already has array-expansion guard before all anchors (noop).")
        return False

    _clipwrite(rel, s2)
    _chmod_x(p)
    print(f"OK: inserted array-expansion guard before {inserted_count} additional anchor(s).")
    return True


def main() -> int:
    changed = _patch_gate_insert_all()
    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
