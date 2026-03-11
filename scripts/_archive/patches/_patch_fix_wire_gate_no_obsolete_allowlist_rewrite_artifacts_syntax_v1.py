from __future__ import annotations

from pathlib import Path

P = Path("scripts/_patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.py")

OLD = """BLOCK = (
    BEGIN
    "bash scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh\\n"
    END
)
"""

NEW = """BLOCK = (
    BEGIN
    + "bash scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh\\n"
    + END
)
"""

def main() -> None:
    if not P.exists():
        raise SystemExit(f"ERROR: missing {P}")

    src = P.read_text(encoding="utf-8")

    if NEW in src:
        print("OK: patcher already fixed")
        return

    if OLD not in src:
        raise SystemExit("ERROR: expected broken BLOCK not found (refuse ambiguous edit)")

    P.write_text(src.replace(OLD, NEW), encoding="utf-8")
    print(f"UPDATED: {P}")

if __name__ == "__main__":
    main()
