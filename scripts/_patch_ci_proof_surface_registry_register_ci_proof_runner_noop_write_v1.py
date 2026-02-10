from __future__ import annotations

from pathlib import Path

PATCHER = Path("scripts/_patch_ci_proof_surface_registry_register_ci_proof_runner_v1.py")

NEEDLE = 'REG.write_text(out, encoding="utf-8")'
REPLACE_BLOCK = """\
    if out == s:
        print("OK: registry already canonical for requested CI proof runner (no-op).")
        return 0

    REG.write_text(out, encoding="utf-8")
    print("OK: registered CI proof runner into BOTH blocks (canonical, sorted, strict).")
    return 0
"""

def main() -> int:
    if not PATCHER.exists():
        raise SystemExit(f"FAIL: missing {PATCHER}")

    s = PATCHER.read_text(encoding="utf-8")

    if NEEDLE not in s:
        raise SystemExit("FAIL: expected write site not found; refusing to patch.")

    if "registry already canonical for requested CI proof runner" in s:
        print("OK: register patcher already has no-op write behavior.")
        return 0

    s2 = s.replace(
        'REG.write_text(out, encoding="utf-8")\n    print("OK: registered CI proof runner into BOTH blocks (canonical, sorted, strict).")\n    return 0',
        REPLACE_BLOCK.rstrip(),
    )

    if s2 == s:
        raise SystemExit("FAIL: patch produced no change unexpectedly (refusing).")

    PATCHER.write_text(s2, encoding="utf-8")
    print("OK: register patcher now no-ops without rewriting file (v1).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
