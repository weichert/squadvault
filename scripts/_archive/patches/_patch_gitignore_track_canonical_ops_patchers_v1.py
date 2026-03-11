#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

BEGIN = "# === SquadVault: track canonical ops patchers (auto) ==="
END   = "# === /SquadVault: track canonical ops patchers (auto) ==="

BLOCK = "\n".join([
    BEGIN,
    "!scripts/_patch_*.py",
    "!scripts/patch_*.sh",
    "!scripts/ops_*.sh",
    END,
]) + "\n"

def main() -> None:
    text = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""

    # No-op if block already present (idempotent).
    if BEGIN in text and END in text:
        print("OK: .gitignore already contains canonical ops patchers allowlist block (v1).")
        return

    # Append with a separating newline if needed.
    out = text
    if out and not out.endswith("\n"):
        out += "\n"
    if out and not out.endswith("\n\n"):
        out += "\n"
    out += BLOCK

    TARGET.write_text(out, encoding="utf-8")
    print("OK: appended canonical ops patchers allowlist block to .gitignore (v1).")

if __name__ == "__main__":
    main()
