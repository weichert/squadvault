from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_v1.py")

OLD = "entries_sorted = sorted({(m, w) for (m, w) in entries}, key=lambda t: t[1])"
NEW = "entries_sorted = sorted({{(m, w) for (m, w) in entries}}, key=lambda t: t[1])"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if NEW in text:
        print("OK: TEMPLATE braces already escaped")
        return

    if OLD not in text:
        raise SystemExit("ERROR: expected TEMPLATE line not found; refuse ambiguous state")

    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("UPDATED:", TARGET)

if __name__ == "__main__":
    main()
