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


# Old "safe under set -u" prefix we introduced:
OLD_PREFIX = 'if [ -n "${t-}" ] && echo "${t-}" | grep -Eq '

# Replace it with a quote-tolerant version (still set -u safe).
# Accept tokens wrapped in any number of ' and/or " characters:
#   ${gp_tests[@]}
#   "${gp_tests[@]}"
#   '${gp_tests[@]}'
#   '"${gp_tests[@]}"'
NEW_LINE = (
    'if [ -n "${t-}" ] && echo "${t-}" | '
    'grep -Eq \'^['"'"']*\\$\\{[A-Za-z0-9_]+_tests\\[@\\]\\}['"'"']*$\' ; then\n'
)


def _patch_guard_in_file(rel: str) -> bool:
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    # If the new pattern is already present, noop.
    if "['\"']*\\$\\{" in s and "_tests\\[@\\]\\}" in s:
        _chmod_x(p)
        print(f"OK: {rel} already quote-tolerant for array-expansion guard (noop).")
        return False

    if OLD_PREFIX not in s:
        # Don't guess: only patch files that we know contain our prior guard form.
        _chmod_x(p)
        print(f"OK: {rel} has no prior array-guard prefix to upgrade (noop).")
        return False

    # Upgrade the first occurrence of the OLD_PREFIX-line to NEW_LINE.
    lines = s.splitlines(keepends=True)
    out: list[str] = []
    replaced = False

    for ln in lines:
        if (not replaced) and ln.lstrip().startswith(OLD_PREFIX):
            out.append(NEW_LINE)
            replaced = True
            continue
        out.append(ln)

    if not replaced:
        raise SystemExit(f"ERROR: could not upgrade guard line in {rel} (refusing).")

    _clipwrite(rel, "".join(out))
    _chmod_x(p)
    print(f"OK: upgraded {rel} array-expansion guard to be quote-tolerant (v2).")
    return True


def _patch_guard_template_in_patcher(rel: str) -> bool:
    """Fix generator patcher so it won’t re-inject the narrow pattern later."""
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    # Idempotence: already quote-tolerant?
    if "['\"']*\\$\\{" in s and "_tests\\[@\\]\\}" in s:
        print(f"OK: {rel} already emits quote-tolerant guard (noop).")
        return False

    if OLD_PREFIX not in s:
        print(f"OK: {rel} has no prior guard template prefix to upgrade (noop).")
        return False

    s2 = s.replace(OLD_PREFIX, 'if [ -n "${t-}" ] && echo "${t-}" | grep -Eq ', 1)
    # Now replace the regex itself if present in the file
    s2 = s2.replace(
        r'\'^"?\$\{[A-Za-z0-9_]+_tests\[@\]\}"?$\'',
        r'\'^['"'"']*\$\{[A-Za-z0-9_]+_tests\[@\]\}['"'"']*$\'',
        1,
    )

    # If the above didn’t hit (because it’s stored differently), do a conservative direct insert:
    if s2 == s:
        # Replace any occurrence of the narrow ^"?\$\{..._tests[@]\}"?$ with the tolerant one.
        s2 = s.replace(
            r'^"?\$\{[A-Za-z0-9_]+_tests\[@\]\}"?$',
            r"^['\"']*\$\{[A-Za-z0-9_]+_tests\[@\]\}['\"']*$",
            1,
        )

    if s2 == s:
        print(f"OK: {rel} unchanged (noop).")
        return False

    _clipwrite(rel, s2)
    print(f"OK: updated {rel} to emit quote-tolerant guard going forward (v2).")
    return True


def main() -> int:
    changed = False

    # The gate definitely has the guard.
    changed |= _patch_guard_in_file("scripts/gate_pytest_tracked_tests_only_v1.sh")

    # This check script may or may not have the marker; patch only if the prefix exists.
    changed |= _patch_guard_in_file("scripts/check_no_pytest_directory_invocation.sh")

    # Update generator patcher so future runs don’t regress.
    changed |= _patch_guard_template_in_patcher("scripts/_patch_fix_pytest_target_parser_allow_array_expansions_v1.py")

    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
