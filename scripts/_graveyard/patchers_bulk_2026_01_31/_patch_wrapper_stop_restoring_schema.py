from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    # Remove the restore block lines (echo + git restore + continuation)
    s2 = re.sub(
        r'\n?echo "Step 1: restore schema to HEAD[^\n]*"\n'
        r'git restore --source=HEAD -- \\\n'
        r'\s*src/squadvault/recaps/writing_room/selection_set_schema_v1\.py\n',
        "\n",
        s,
        count=1,
    )

    # Renumber the next echo if present
    s2 = s2.replace('echo "Step 2: patch intake_v1 to use ExcludedSignal(details=...)"',
                    'echo "Step 1: patch intake_v1 to use ExcludedSignal(details=...)"')

    if s2 == s:
        raise SystemExit("ERROR: did not find expected schema-restore block; refusing to patch.")

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: patched {TARGET.relative_to(ROOT)} (no longer restores schema to HEAD each run)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
