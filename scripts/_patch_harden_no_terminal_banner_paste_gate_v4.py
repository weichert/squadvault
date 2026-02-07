from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_no_terminal_banner_paste_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: expected gate not found: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    marker = "# High-signal banner patterns (anchored to start-of-line to avoid matching literals in code/comments)."
    if marker in text:
        print("OK: v4 comment already present (idempotent).")
        return

    replacement = """# High-signal banner patterns (anchored to start-of-line to avoid matching literals in code/comments).
# NOTE:
#   Anchoring with ^ is intentional.
#   This gate must detect *pasted terminal output*, not pattern strings
#   embedded inside patchers, docs, or gate source itself.
"""

    if "# High-signal banner patterns" not in text:
        raise SystemExit("ERROR: expected pattern comment block not found; refusing to patch.")

    text = text.replace(
        "# High-signal banner patterns (anchored to start-of-line to avoid matching literals in code/comments).",
        replacement.rstrip(),
        1,
    )

    TARGET.write_text(text, encoding="utf-8")
    print("OK: added v4 clarification comment to terminal banner gate.")

if __name__ == "__main__":
    main()
