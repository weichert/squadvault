from __future__ import annotations

from pathlib import Path
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


def _patch_prove_ci_banner() -> bool:
    root = _repo_root()
    p = root / "scripts" / "prove_ci.sh"
    if not p.exists():
        raise SystemExit("ERROR: scripts/prove_ci.sh not found")

    s = _read(p)
    old = 'echo "=== Gate: No mapfile/readarray in scripts/ (v1) ==="\n'
    new = 'echo "=== Gate: Bash 3.2 builtin compatibility (v1) ==="\n'

    if old not in s:
        # already updated (or formatted differently)
        if new in s:
            print("OK: prove_ci banner already canonical (noop).")
            return False
        # If neither string is present, do not guess — fail loudly.
        raise SystemExit("ERROR: could not find expected prove_ci banner line to update (refusing).")

    s2 = s.replace(old, new)
    _clipwrite("scripts/prove_ci.sh", s2)
    print("OK: updated prove_ci banner to avoid mapfile/readarray tokens (v1).")
    return True


def _patch_add_gate_wiring_block() -> bool:
    root = _repo_root()
    p = root / "scripts" / "_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py"
    if not p.exists():
        raise SystemExit("ERROR: scripts/_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py not found")

    s = _read(p)

    old = 'echo "=== Gate: No mapfile/readarray in scripts/ (v1) ==="\\n'
    new = 'echo "=== Gate: Bash 3.2 builtin compatibility (v1) ==="\\n'

    if old not in s:
        if new in s:
            print("OK: add-gate patcher wiring block already canonical (noop).")
            return False
        raise SystemExit("ERROR: could not find expected wiring echo line in add-gate patcher (refusing).")

    s2 = s.replace(old, new)
    _clipwrite("scripts/_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py", s2)
    print("OK: updated add-gate patcher wiring echo to avoid mapfile/readarray tokens (v1).")
    return True


def main() -> int:
    changed = False
    changed |= _patch_prove_ci_banner()
    changed |= _patch_add_gate_wiring_block()

    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
