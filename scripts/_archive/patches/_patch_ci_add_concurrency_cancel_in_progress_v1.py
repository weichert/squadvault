from __future__ import annotations

import re
from pathlib import Path

TARGET = Path(".github/workflows/ci.yml")
MARK = "ci_add_concurrency_cancel_in_progress_v1"

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not TARGET.exists():
        die(f"FAIL: missing workflow: {TARGET}")

    s = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    # If already present, no-op.
    if "concurrency:" in s and "cancel-in-progress:" in s and "ci-${{ github.ref }}" in s:
        print("NO-OP: concurrency block already present")
        return

    if MARK in s:
        print("NO-OP: already patched (marker present)")
        return

    block = (
        "\nconcurrency:\n"
        "  group: ci-${{ github.ref }}\n"
        f"  cancel-in-progress: true  # {MARK}\n"
    )

    m_jobs = re.search(r"(?m)^jobs:\s*$", s)
    if not m_jobs:
        die("FAIL: could not find top-level 'jobs:' in workflow")

    insert_at = m_jobs.start()
    out = s[:insert_at].rstrip() + block + "\n\n" + s[insert_at:].lstrip()

    TARGET.write_text(out, encoding="utf-8", newline="\n")
    print("OK: added concurrency cancel-in-progress block (v1)")

if __name__ == "__main__":
    main()
