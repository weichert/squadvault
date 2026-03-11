from __future__ import annotations

from pathlib import Path

REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

HEADER = "## Proof Runners (invoked by scripts/prove_ci.sh)"
ENTRY = "- scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh — Proof: terminal banner paste gate behavior (v1)"

def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit(f"ERROR: missing registry: {REGISTRY}")

    lines = REGISTRY.read_text(encoding="utf-8").splitlines(keepends=True)

    try:
        h = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == HEADER)
    except StopIteration:
        raise SystemExit(f"ERROR: could not find header in registry: {HEADER!r}")

    # If already present anywhere, no-op.
    if any(ln.rstrip("\n") == ENTRY for ln in lines):
        print("OK: registry already contains terminal banner proof runner (idempotent).")
        return

    # Insert deterministically as the first bullet in the Proof Runners section.
    # Find insertion point: first non-blank line after header; if that's already a bullet, insert before it.
    # If section is empty, insert after the header + any blank lines.
    insert_at = h + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    # If we ran into next section header, we still insert before it (empty section case).
    new_line = ENTRY + "\n"
    lines.insert(insert_at, new_line)

    REGISTRY.write_text("".join(lines), encoding="utf-8")
    print("OK: inserted terminal banner proof runner into registry.")

if __name__ == "__main__":
    main()
