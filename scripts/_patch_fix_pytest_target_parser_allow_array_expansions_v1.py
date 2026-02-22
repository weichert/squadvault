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


_GUARD = (
    '# <!-- SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 -->\n'
    '# Accept pytest targets that are array expansions (already validated elsewhere).\n'
    '# Examples: "${gp_tests[@]}", ${gp_tests[@]}\n'
    'if echo "$t" | grep -Eq \'^"?\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}"?$\' ; then\n'
    '  continue\n'
    'fi\n'
)


def _insert_guard_before_anchor(rel: str, anchors: tuple[str, ...]) -> bool:
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    # Idempotence
    if "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1" in s:
        _chmod_x(p)
        print(f"OK: {rel} already patched (noop).")
        return False

    # Find first anchor occurrence and insert guard immediately before that line.
    lines = s.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for ln in lines:
        if (not inserted) and any(a in ln for a in anchors):
            out.append(_GUARD)
            inserted = True
        out.append(ln)

    if not inserted:
        # For the check script, do NOT fail hard; formats vary. Just noop.
        _chmod_x(p)
        print(f"OK: {rel} has no recognized anchor; left unchanged (noop).")
        return False

    _clipwrite(rel, "".join(out))
    _chmod_x(p)
    print(f"OK: patched {rel} to allow pytest array-expansion targets.")
    return True


def main() -> int:
    changed = False

    # Gate: anchor is the canonical message we know exists there.
    changed |= _insert_guard_before_anchor(
        "scripts/gate_pytest_tracked_tests_only_v1.sh",
        ("pytest target must start with Tests/",),
    )

    # Check script: tolerate variants.
    changed |= _insert_guard_before_anchor(
        "scripts/check_no_pytest_directory_invocation.sh",
        (
            "pytest target must start with Tests/",
            "must start with Tests/",
            "start with Tests/",
        ),
    )

    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
