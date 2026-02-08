from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py")

OLD_1 = 'out.append(f"{m}\\\\n")'
NEW_1 = 'out.append(f"{{m}}\\\\n")'

OLD_2 = 'out.append(f\'  "{w}"\\\\n\\\\n\')'
NEW_2 = 'out.append(f\'  "{{w}}"\\\\n\\\\n\')'

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # Idempotence: if already fixed, no-op.
    if NEW_1 in text and NEW_2 in text:
        print("OK: TEMPLATE f-string braces already escaped")
        return

    if OLD_1 not in text:
        raise SystemExit("ERROR: expected OLD_1 not found; refuse ambiguous state")
    if OLD_2 not in text:
        raise SystemExit("ERROR: expected OLD_2 not found; refuse ambiguous state")

    text = text.replace(OLD_1, NEW_1).replace(OLD_2, NEW_2)
    TARGET.write_text(text, encoding="utf-8")
    print("UPDATED:", TARGET)

if __name__ == "__main__":
    main()
