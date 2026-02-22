from __future__ import annotations

from pathlib import Path
import re
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


def _portable_targets_block_prove_only() -> str:
    # bash 3.2 compatible: no mapfile/readarray
    return r'''TARGETS=()
while IFS= read -r f; do
  [ -n "$f" ] && TARGETS+=("$f")
done < <(
  git ls-files "scripts/prove_*.sh"
)'''


def _patch_gate_file() -> None:
    root = _repo_root()
    gate = root / "scripts" / "gate_pytest_tracked_tests_only_v1.sh"
    if not gate.exists():
        raise SystemExit("ERROR: scripts/gate_pytest_tracked_tests_only_v1.sh not found")

    s = _read(gate)

    # Idempotence: if already prove-only, noop
    if 'git ls-files "scripts/prove_*.sh"' in s and "TARGETS=(" in s:
        _chmod_x(gate)
        print("OK: gate already prove-only scope (noop).")
        return

    desired_block = _portable_targets_block_prove_only() + "\n"

    # 1) mapfile/readarray form (older)
    s2 = re.sub(
        r'(?s)mapfile\s+-t\s+TARGETS\s+<\s*<\(\s*\n.*?\n\)\s*\n',
        desired_block,
        s,
        count=1,
    )

    # 2) portable v1 while-read form (format tolerant)
    if s2 == s:
        s2 = re.sub(
            r'(?s)TARGETS=\(\)\s*\n.*?done[^\n]*<\s*<\(\s*\n.*?\n\)\s*\n',
            desired_block,
            s,
            count=1,
        )

    # 3) last-resort: replace only the inner command list inside the process substitution
    #    within the first TARGETS loader we can find.
    if s2 == s:
        m = re.search(r'(?s)(TARGETS=\(\)\s*\n.*?done[^\n]*<\s*<\()\s*\n(.*?)(\n\)\s*\n)', s)
        if m:
            s2 = s[: m.start(1)] + m.group(1) + "\n  git ls-files \"scripts/prove_*.sh\"\n" + m.group(3) + s[m.end(3) :]
        else:
            raise SystemExit("ERROR: could not replace TARGETS block in gate (unexpected format).")

    _clipwrite("scripts/gate_pytest_tracked_tests_only_v1.sh", s2)
    _chmod_x(gate)
    print("OK: updated gate scope: scan only scripts/prove_*.sh (v2).")


def _patch_add_gate_patcher() -> None:
    root = _repo_root()
    p = root / "scripts" / "_patch_add_gate_pytest_tracked_tests_only_v1.py"
    if not p.exists():
        raise SystemExit("ERROR: scripts/_patch_add_gate_pytest_tracked_tests_only_v1.py not found")

    s = _read(p)

    # Idempotence: if already prove-only in emitted gate body, noop
    if 'git ls-files "scripts/prove_*.sh"' in s:
        print("OK: add-gate patcher already prove-only scope (noop).")
        return

    desired_block = _portable_targets_block_prove_only() + "\n"

    s2 = s

    # mapfile variant
    s2 = re.sub(
        r'(?s)mapfile\s+-t\s+TARGETS\s+<\s*<\(\s*\n.*?\n\)\s*\n',
        desired_block,
        s2,
        count=1,
    )

    # portable variant
    if s2 == s:
        s2 = re.sub(
            r'(?s)TARGETS=\(\)\s*\n.*?done[^\n]*<\s*<\(\s*\n.*?\n\)\s*\n',
            desired_block,
            s2,
            count=1,
        )

    if s2 == s:
        # If we can't find the gate body structure safely, refuse.
        raise SystemExit("ERROR: could not update add-gate patcher TARGETS scope (unexpected format).")

    _clipwrite("scripts/_patch_add_gate_pytest_tracked_tests_only_v1.py", s2)
    print("OK: updated add-gate patcher to emit prove-only TARGETS scope.")


def main() -> int:
    _patch_gate_file()
    _patch_add_gate_patcher()

    # Smoke: re-apply add-gate wrapper twice (idempotence)
    wrapper = _repo_root() / "scripts" / "patch_add_gate_pytest_tracked_tests_only_v1.sh"
    if wrapper.exists():
        subprocess.run(["bash", str(wrapper)], check=True, cwd=str(_repo_root()))
        subprocess.run(["bash", str(wrapper)], check=True, cwd=str(_repo_root()))
        print("OK: re-applied add-gate wrapper twice (idempotence smoke).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
