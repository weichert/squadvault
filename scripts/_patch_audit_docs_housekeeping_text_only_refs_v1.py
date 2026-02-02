from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/audit_docs_housekeeping_v1.sh")

OLD = r'grep -Roh "docs/[A-Za-z0-9_./-]*" docs 2>/dev/null | sort -u > .local_audit/docs_path_mentions.txt || true'
NEW = r"grep -Roh --include='*.md' --include='*.txt' \"docs/[A-Za-z0-9_./-]*\" docs 2>/dev/null \\\n  | sort -u > .local_audit/docs_path_mentions.txt || true"

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if "--include='*.md'" in s and "--include='*.txt'" in s:
        print("OK: audit already scans text files only")
        return
    if OLD not in s:
        raise SystemExit("ERROR: could not locate grep path-mentions line to patch")
    TARGET.write_text(s.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK: patched audit to scan md/txt only for docs/* path mentions")

if __name__ == "__main__":
    main()
