from __future__ import annotations

from pathlib import Path

ALLOW = Path("scripts/patch_idempotence_allowlist_v1.txt")

OLD = "scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh"
NEW = "scripts/patch_index_ci_proof_surface_registry_discoverability_v3.sh"

def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing allowlist: {ALLOW}")

    raw = ALLOW.read_text(encoding="utf-8").splitlines()
    lines = [ln.strip() for ln in raw if ln.strip()]

    if NEW in lines and OLD not in lines:
        print("OK: allowlist already uses v3 (idempotent).")
        return

    out = [ln for ln in lines if ln != OLD]
    if NEW not in out:
        out.append(NEW)

    out = sorted(set(out))
    ALLOW.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("OK: updated idempotence allowlist to use registry index v3.")

if __name__ == "__main__":
    main()
