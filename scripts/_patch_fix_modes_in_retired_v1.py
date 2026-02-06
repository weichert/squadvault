from __future__ import annotations

import os
from pathlib import Path

RET = Path("scripts/_retired")

def main() -> None:
    if not RET.exists():
        print("OK: no scripts/_retired/ directory; nothing to do")
        return

    changed = 0
    for p in sorted(RET.iterdir()):
        if not p.is_file():
            continue
        if p.suffix == ".sh":
            # Ensure executable for user/group/other: 755
            desired = 0o755
            current = p.stat().st_mode & 0o777
            if current != desired:
                os.chmod(p, desired)
                changed += 1

    print(f"OK: fixed modes on {changed} retired .sh files (ensured 755)")

if __name__ == "__main__":
    main()
