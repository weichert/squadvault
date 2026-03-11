from __future__ import annotations

import os
from pathlib import Path
import stat

TARGET = Path("scripts/gate_no_xtrace_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    st = TARGET.stat()
    mode = stat.S_IMODE(st.st_mode)
    new_mode = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

    if new_mode == mode:
        print("OK: gate_no_xtrace_v1.sh already executable (no-op).")
        return

    os.chmod(TARGET, new_mode)
    print(f"OK: set executable bit on {TARGET} (mode {oct(mode)} -> {oct(new_mode)})")

if __name__ == "__main__":
    main()
