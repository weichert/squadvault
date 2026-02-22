from __future__ import annotations

from pathlib import Path
import re
import subprocess
import stat


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


def _portable_targets_block() -> str:
    # bash 3.2 compatible: no mapfile/readarray
    return r'''TARGETS=()
while IFS= read -r f; do
  [ -n "$f" ] && TARGETS+=("$f")
done < <(
  git ls-files \
    "scripts/prove_*.sh" \
    "scripts/gate_*.sh" \
    "scripts/check_*.sh"
)'''


def _patch_gate_file() -> None:
    root = _repo_root()
    gate = root / "scripts" / "gate_pytest_tracked_tests_only_v1.sh"
    if not gate.exists():
        raise SystemExit("ERROR: scripts/gate_pytest_tracked_tests_only_v1.sh not found")

    s = _read(gate)
    if "mapfile -t TARGETS" not in s:
        _chmod_x(gate)
        print("OK: gate already does not use mapfile (noop).")
        return

    # Replace the mapfile block with portable block (best-effort exact match)
    s2 = re.sub(
        r'mapfile -t TARGETS < <\(\n\s*git ls-files \\\n(?:.*\n)*?\)\n',
        _portable_targets_block() + "\n",
        s,
        flags=re.MULTILINE,
    )
    if s2 == s:
        raise SystemExit("ERROR: could not replace mapfile block in gate (unexpected format).")

    _clipwrite("scripts/gate_pytest_tracked_tests_only_v1.sh", s2)
    _chmod_x(gate)
    print("OK: rewrote gate to avoid mapfile (bash 3.2 compatible).")


def _patch_add_gate_patcher() -> None:
    root = _repo_root()
    p = root / "scripts" / "_patch_add_gate_pytest_tracked_tests_only_v1.py"
    if not p.exists():
        raise SystemExit("ERROR: scripts/_patch_add_gate_pytest_tracked_tests_only_v1.py not found")

    s = _read(p)
    if "mapfile -t TARGETS" not in s:
        print("OK: add-gate patcher already does not use mapfile (noop).")
        return

    # Replace the mapfile snippet inside the raw _GATE_BODY string.
    # We do a conservative substitution of that exact line with the portable block.
    portable = _portable_targets_block()

    # In the python raw string, backslashes are literal; we just insert the bash text as-is.
    s2 = s.replace(
        'mapfile -t TARGETS < <(\n'
        '  git ls-files \\\n'
        '    "scripts/prove_*.sh" \\\n'
        '    "scripts/gate_*.sh" \\\n'
        '    "scripts/check_*.sh"\n'
        ')\n',
        portable + "\n",
    )

    if s2 == s:
        # Fallback: if formatting differs slightly, try a regex replace within the file text.
        s2 = re.sub(
            r'mapfile -t TARGETS < <\(\n\s*git ls-files \\\n\s*"scripts/prove_\*\.sh" \\\n\s*"scripts/gate_\*\.sh" \\\n\s*"scripts/check_\*\.sh"\n\s*\)\n',
            portable + "\n",
            s,
        )

    if s2 == s:
        raise SystemExit("ERROR: could not update mapfile block inside add-gate patcher (unexpected format).")

    _clipwrite("scripts/_patch_add_gate_pytest_tracked_tests_only_v1.py", s2)
    print("OK: updated add-gate patcher _GATE_BODY to avoid mapfile.")


def main() -> int:
    _patch_gate_file()
    _patch_add_gate_patcher()

    # Re-apply the canonical wrapper to ensure gate content matches patcher output (idempotent check)
    wrapper = _repo_root() / "scripts" / "patch_add_gate_pytest_tracked_tests_only_v1.sh"
    if wrapper.exists():
        subprocess.run(["bash", str(wrapper)], check=True, cwd=str(_repo_root()))
        subprocess.run(["bash", str(wrapper)], check=True, cwd=str(_repo_root()))
        print("OK: re-applied add-gate wrapper twice (idempotence smoke).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
