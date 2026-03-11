from __future__ import annotations

from pathlib import Path

REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END = "<!-- CI_PROOF_RUNNERS_END -->"

ENTRY = "- scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh — Proof: allowlisted patch wrappers are no-op under `SV_IDEMPOTENCE_MODE=1`.\n"

def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit(f"ERROR: missing {REGISTRY}")

    text = REGISTRY.read_text(encoding="utf-8")
    if ENTRY in text:
        print("OK: registry already contains idempotence allowlist proof entry (v1).")
        return

    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: registry is missing CI_PROOF_RUNNERS_BEGIN/END markers.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    # Insert entry at end of mid block, keeping a trailing newline.
    if not mid.endswith("\n"):
        mid += "\n"
    mid2 = mid + ENTRY

    REGISTRY.write_text(pre + BEGIN + mid2 + END + post, encoding="utf-8")
    print("OK: added idempotence allowlist proof entry to registry (v1).")

if __name__ == "__main__":
    main()
