from __future__ import annotations
from pathlib import Path

TARGET = Path("scripts/audit_docs_housekeeping_v1.sh")

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    candidates = [
        'for p in root.rglob("*"):',
        "for p in root.rglob('*'):",
    ]
    for needle in candidates:
        if needle in s:
            if "for p in sorted(root.rglob" in s:
                print("OK: rglob already sorted")
                return
            repl = needle.replace("for p in ", "for p in sorted(")[:-1] + "):"
            # Example: for p in sorted(root.rglob("*")):
            s2 = s.replace(needle, repl, 1)
            TARGET.write_text(s2, encoding="utf-8")
            print("OK: patched audit_docs_housekeeping to sort rglob")
            return

    raise SystemExit("ERROR: could not locate rglob loop in scripts/audit_docs_housekeeping_v1.sh")

if __name__ == "__main__":
    main()
