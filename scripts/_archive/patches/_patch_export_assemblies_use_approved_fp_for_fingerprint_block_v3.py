from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")
MARKER = "SV_PATCH_EXPORT_ASSEMBLIES_USE_APPROVED_FP_FOR_FINGERPRINT_BLOCK_V3"

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARKER in s:
        print(f"OK: already patched: {TARGET} ({MARKER})")
        return

    needle = "blocks = extract_blocks_from_neutral(neutral)"
    if needle not in s:
        raise SystemExit(f"ERROR: could not find anchor line: {needle}")

    insert = f"""{needle}

    # {MARKER}
    # The assembly's canonical fingerprint block must reflect the APPROVED artifact selection_fingerprint
    # when it is a valid 64-lower-hex value. The neutral render output may contain a placeholder
    # (e.g., 'test-fingerprint'), which is not acceptable for NAC.
    _approved_fp = str(getattr(approved, "selection_fingerprint", "") or "").strip()
    if HEX64_RE.match(_approved_fp):
        blocks["FINGERPRINT"] = f"Selection fingerprint: {{_approved_fp}}\\n"
"""

    s2 = s.replace(needle, insert, 1)

    # Ensure `re` is imported (it already is in many files; add only if missing).
    # We used HEX64_RE at module scope; it must exist. We'll inject it near top-level constants/imports.
    if "HEX64_RE" not in s2:
        # Insert HEX64_RE just after imports section by finding first blank line after imports.
        # Conservative: place it right before first function def in file.
        m = re.search(r"\n\ndef\s", s2)
        if not m:
            raise SystemExit("ERROR: could not locate insertion point for HEX64_RE")
        i = m.start() + 1
        s2 = s2[:i] + "HEX64_RE = re.compile(r\"^[0-9a-f]{64}$\")\n\n" + s2[i:]

    # Ensure `re` is imported.
    if re.search(r"^import re$", s2, flags=re.MULTILINE) is None:
        # Add `import re` after the first block of imports (after argparse/json/os/sys/subprocess/etc).
        # Insert after last contiguous import line at top.
        lines = s2.splitlines(True)
        insert_at = None
        for idx, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = idx + 1
                continue
            # stop at first non-import, non-shebang, non-comment, non-empty
            if insert_at is not None and line.strip() and not line.lstrip().startswith("#"):
                break
        if insert_at is None:
            raise SystemExit("ERROR: could not find import section to add `import re`")
        lines.insert(insert_at, "import re\n")
        s2 = "".join(lines)

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: patched {TARGET} (fingerprint block uses approved.selection_fingerprint when valid).")


if __name__ == "__main__":
    main()
