#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

# We replace the whole block starting at the comment and ending at the matching 'fi'.
BLOCK_RE = re.compile(
    r"""
(?P<prefix>
^[ \t]*#\ Golden\ path\ uses\ local\ db\ by\ default;[^\n]*\n
^[ \t]*#\ If\ prove_golden_path\.sh[^\n]*\n
^[ \t]*if\ bash\ scripts/prove_golden_path\.sh\ --help[^\n]*\n
)
(?P<body>.*?)
^[ \t]*fi[ \t]*\n
""",
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)

NEW_BLOCK = """\
# Golden path uses local db by default; point it at the fixture explicitly if supported.
# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.
if bash scripts/prove_golden_path.sh --help 2>/dev/null | grep -q -- '--db'; then
  SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh --db "${WORK_DB}" --league-id 70985 --season 2024 --week-index 6
else
  SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh
fi
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    m = BLOCK_RE.search(text)
    if not m:
        raise SystemExit("ERROR: could not locate golden path block to rewrite")

    # Replace the entire matched region with NEW_BLOCK (keeps file structure stable)
    start, end = m.span()
    out = text[: start] + NEW_BLOCK + text[end :]

    TARGET.write_text(out, encoding="utf-8")

    # Postconditions:
    # 1) bash -n will be checked in wrapper
    # 2) block contains SV_STRICT_EXPORTS=1 twice
    post = TARGET.read_text(encoding="utf-8")
    if post.count("SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh") < 2:
        raise SystemExit("ERROR: postcondition failed: expected two strict golden path invocations")

    print("=== Patch: rewrite prove_ci golden path block strict (v1) ===")
    print(f"target={TARGET}")
    print("rewrote_block=yes")

if __name__ == "__main__":
    main()
