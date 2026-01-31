#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

TARGET = Path(".gitignore")

BEGIN = "# === SquadVault: track canonical ops patchers (auto) ==="
END   = "# === /SquadVault: track canonical ops patchers (auto) ==="

# The ONLY python patchers we consider "canonical" for ops right now.
ALLOWLIST = [
    "!scripts/_patch_fix_ops_orchestrate_commit_before_prove_v1.py",
    "!scripts/_patch_fix_ops_orchestrate_idempotency_semantics_v1.py",
    "!scripts/_patch_fix_ops_orchestrate_wrapper_path_normalization_v1.py",
    "!scripts/_patch_gitignore_allow_ops_orchestrate_patchers_v1.py",
    "!scripts/_patch_gitignore_allow_ops_orchestrate_path_norm_patcher_v1.py",
    "!scripts/_patch_gitignore_track_canonical_ops_patchers_v1.py",
]

BLOCK_LINES = [
    BEGIN,
    "# NOTE: Do NOT use broad globs like !scripts/_patch_*.py (will vacuum historical patchers).",
    "# Canonical allowlist only:",
    *ALLOWLIST,
    "# Shell wrappers are canonical by convention:",
    "!scripts/patch_*.sh",
    "!scripts/ops_*.sh",
    END,
    "",
]
BLOCK = "\n".join(BLOCK_LINES)

def main() -> None:
    text = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n")

    # Replace existing block if present; otherwise append.
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?",
        flags=re.DOTALL,
    )

    if pattern.search(text):
        out = pattern.sub(BLOCK, text)
        if out == text:
            print("OK: .gitignore canonical ops patchers block already pinned (v1).")
            return
        TARGET.write_text(out, encoding="utf-8")
        print("OK: rewrote canonical ops patchers block in .gitignore (v1).")
        return

    # Append with spacing.
    out = text
    if out and not out.endswith("\n"):
        out += "\n"
    if out and not out.endswith("\n\n"):
        out += "\n"
    out += BLOCK
    TARGET.write_text(out, encoding="utf-8")
    print("OK: appended canonical ops patchers block to .gitignore (v1).")

if __name__ == "__main__":
    main()
