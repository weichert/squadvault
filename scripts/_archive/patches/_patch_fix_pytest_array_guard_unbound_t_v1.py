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


SAFE_LINE = (
    'if [ -n "${t-}" ] && echo "${t-}" | '
    'grep -Eq \'^"?\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}"?$\' ; then\n'
)


def _patch_guard_in_file(rel: str) -> bool:
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    if "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1" not in s:
        _chmod_x(p)
        print(f"OK: {rel} has no SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1 marker (noop).")
        return False

    # Idempotence: already safe?
    if SAFE_LINE in s:
        _chmod_x(p)
        print(f"OK: {rel} guard already set -u safe (noop).")
        return False

    # Replace the first occurrence of the unsafe 'if echo "$t" | grep -Eq ...' with the safe variant.
    old_frag = 'if echo "$t" | grep -Eq '
    if old_frag not in s:
        raise SystemExit(f"ERROR: expected unsafe guard line not found in {rel} (refusing).")

    lines = s.splitlines(keepends=True)
    out: list[str] = []
    replaced = False

    for ln in lines:
        if (not replaced) and ln.lstrip().startswith("if echo \"$t\" | grep -Eq "):
            out.append(SAFE_LINE)
            replaced = True
            continue
        out.append(ln)

    if not replaced:
        raise SystemExit(f"ERROR: could not replace unsafe guard line in {rel} (refusing).")

    _clipwrite(rel, "".join(out))
    _chmod_x(p)
    print(f"OK: updated {rel} guard to be set -u safe.")
    return True


def _patch_guard_template_in_patcher(rel: str) -> bool:
    """Also fix the generator patcher so it won't re-inject the unsafe guard later."""
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    # Idempotence: already uses ${t-}
    if "${t-}" in s and "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1" in s:
        print(f"OK: {rel} already emits set -u safe guard (noop).")
        return False

    # Replace the guard line inside the python patcher content.
    if 'if echo "$t" | grep -Eq' not in s:
        print(f"OK: {rel} has no unsafe guard template to update (noop).")
        return False

    s2 = s.replace(
        'if echo "$t" | grep -Eq ',
        'if [ -n "${t-}" ] && echo "${t-}" | grep -Eq ',
        1,
    )

    if s2 == s:
        print(f"OK: {rel} already updated (noop).")
        return False

    _clipwrite(rel, s2)
    print(f"OK: updated {rel} to emit set -u safe guard going forward.")
    return True


def main() -> int:
    changed = False
    changed |= _patch_guard_in_file("scripts/gate_pytest_tracked_tests_only_v1.sh")
    changed |= _patch_guard_in_file("scripts/check_no_pytest_directory_invocation.sh")  # may noop
    changed |= _patch_guard_template_in_patcher("scripts/_patch_fix_pytest_target_parser_allow_array_expansions_v1.py")

    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
