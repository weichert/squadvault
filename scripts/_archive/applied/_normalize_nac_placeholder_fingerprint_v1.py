from __future__ import annotations

import sys
from pathlib import Path

PLACEHOLDER_LINE = "Selection fingerprint: test-fingerprint"


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        die("usage: _normalize_nac_placeholder_fingerprint_v1.py <assembly_path> <fp64>")

    path = Path(argv[1])
    fp = argv[2]

    if not path.exists():
        die(f"assembly not found: {path}")

    # Validate fp is exactly 64 lowercase hex
    import re
    if not re.fullmatch(r"[0-9a-f]{64}", fp):
        die("fp must be exactly 64 lowercase hex")

    text = path.read_text(encoding="utf-8")
    count = text.count(PLACEHOLDER_LINE)

    if count == 0:
        # No-op: nothing to normalize.
        return 0

    if count != 1:
        die(f"placeholder fingerprint line appears {count} times; expected exactly 1")

    new_text = text.replace(PLACEHOLDER_LINE, f"Selection fingerprint: {fp}")

    # Atomic-ish write: write to sibling temp then replace.
    tmp = path.with_suffix(path.suffix + ".sv_tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
