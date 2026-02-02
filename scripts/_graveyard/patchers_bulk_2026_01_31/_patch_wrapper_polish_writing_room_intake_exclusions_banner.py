from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    # 1) Fix title banner
    s2 = s
    s2 = s2.replace(
        'echo "=== Patch: Writing Room intake_v1 ExcludedSignal(details) + restore schema ==="',
        'echo "=== Patch: Writing Room intake_v1 exclusions (schema-aligned) ==="',
    )

    # 2) Fix any lingering "restore schema" wording anywhere
    s2 = s2.replace(" + restore schema", "")
    s2 = s2.replace("restore schema", "schema-aligned")

    # 3) Normalize step text (keep minimal, truthful)
    # We only touch echo lines (safe).
    s2 = re.sub(
        r'echo "Step\s*\d+:\s*patch intake_v1 to use ExcludedSignal\(details=\.\.\.\)"',
        'echo "Step 1: patch intake_v1 ExcludedSignal(details=...)"',
        s2,
    )

    # If it has any "Step 2/3 run tests" echoes, normalize to Step 2
    s2 = re.sub(
        r'echo "Step\s*\d+:\s*run tests.*"',
        'echo "Step 2: run tests"',
        s2,
    )

    # 4) Small readability: ensure a blank line before running tests (if missing)
    if 'echo "Step 2: run tests"' in s2:
        # Insert a blank echo right after Step 2 line if not present
        s2 = re.sub(
            r'(echo "Step 2: run tests"\n)(?!echo\s*$)',
            r'\1echo\n',
            s2,
            count=1,
        )

    if s2 == s:
        print("OK: wrapper already polished; nothing to patch.")
        return 0

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: polished {TARGET.relative_to(ROOT)}")
    print("Next:")
    print("  ./scripts/patch_writing_room_intake_exclusions_v1.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
