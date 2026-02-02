from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

START = "# === SquadVault: track canonical ops patchers (auto) ==="
END   = "# === /SquadVault: track canonical ops patchers (auto) ==="

LINE = "!scripts/_patch_prove_eal_remove_redundant_pytest_run_v1.py"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if START not in s or END not in s:
        raise SystemExit("ERROR: could not locate canonical ops patchers block markers")

    pre, rest = s.split(START, 1)
    block, post = rest.split(END, 1)

    # Already present?
    if LINE in block:
        print("OK: .gitignore already allowlists prove_eal redundant pytest patcher (v1).")
        return

    lines = block.splitlines()

    # Insert after the "Canonical allowlist only:" line if present, else near top of block.
    insert_at = None
    for i, ln in enumerate(lines):
        if ln.strip() == "# Canonical allowlist only:":
            insert_at = i + 1
            break
    if insert_at is None:
        insert_at = 0

    lines.insert(insert_at, LINE)

    new_block = "\n".join(lines).rstrip("\n") + "\n"
    out = pre + START + new_block + END + post
    TARGET.write_text(out, encoding="utf-8")
    print("OK: added allowlist entry for prove_eal redundant pytest patcher (v1).")

if __name__ == "__main__":
    main()
