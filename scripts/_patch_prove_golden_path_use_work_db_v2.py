from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
MARK = "prove_golden_path_use_work_db_v2"

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not TARGET.exists():
        die(f"FAIL: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    if MARK in s:
        print("NO-OP: already patched (marker present)")
        return

    # Match: DB="${DB:-.local_squadvault.sqlite}"  (allow whitespace, quotes)
    pat = re.compile(
        r'(?m)^(?P<indent>[ \t]*)DB="\$\{DB:-\.local_squadvault\.sqlite\}"\s*$'
    )
    m = pat.search(s)
    if not m:
        # Give helpful context
        hits = []
        for i, line in enumerate(s.splitlines(), start=1):
            if "DB=" in line or ".local_squadvault" in line:
                hits.append(f"{i}:{line}")
            if len(hits) >= 25:
                break
        die(
            "FAIL: could not find expected DB default line: DB=\"${DB:-.local_squadvault.sqlite}\"\n"
            "First lines mentioning 'DB=' or '.local_squadvault' were:\n" + "\n".join(hits)
        )

    indent = m.group("indent")
    repl = (
        f'{indent}DB="${{WORK_DB:-${{CI_WORK_DB:-${{DB:-.local_squadvault.sqlite}}}}}}"'
        f'  # {MARK}'
    )
    out = s[:m.start()] + repl + s[m.end():]

    TARGET.write_text(out, encoding="utf-8", newline="\n")
    print("OK: prove_golden_path now prefers WORK_DB/CI_WORK_DB (v2)")

if __name__ == "__main__":
    main()
