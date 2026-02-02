from __future__ import annotations

from pathlib import Path


TARGET = Path("scripts/check_no_pytest_directory_invocation.sh")
MARKER = "SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)\n"


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("OK: already patched (v2 marker present).")
        return

    # We patch the detection loop in-place by replacing the 'case "$line" in *pytest* )' arm
    # with stricter executable pytest detection + ignore echo/printf.
    old = """\
    # Only consider lines that appear to run pytest.
    # Covers:
    #   pytest ...
    #   python -m pytest ...
    #   scripts/py -m pytest ...
    case "$line" in
      *pytest* )
        # If the line references Tests but not .py, it's almost certainly a directory invocation.
        # This intentionally fails closed.
        if echo "$line" | grep -q 'Tests' && ! echo "$line" | grep -q '\\.py'; then
"""

    if old not in text:
        raise SystemExit("ERROR: expected block not found in gate script (cannot patch safely)")

    new = """\
    # SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)
    # Only consider lines that appear to EXECUTE pytest.
    # - Ignore echo/printf lines (they may mention 'pytest' in log text)
    # - Match either: command starts with pytest, or contains '-m pytest'
    if echo "$line" | grep -Eq '^[[:space:]]*(echo|printf)[[:space:]]'; then
      continue
    fi

    if echo "$line" | grep -Eq '^[[:space:]]*pytest[[:space:]]' || echo "$line" | grep -Eq '[[:space:]]-m[[:space:]]+pytest[[:space:]]'; then
      # If the line references Tests but not .py, it's almost certainly a directory invocation.
      # This intentionally fails closed.
      if echo "$line" | grep -q 'Tests' && ! echo "$line" | grep -q '\\.py'; then
"""

    patched = text.replace(old, new)

    # Remove the trailing ';; esac' that belonged to the old case arm.
    tail = """\
        ;;
    esac
"""
    if tail not in patched:
        raise SystemExit("ERROR: expected case/esac tail not found after replacement (cannot patch safely)")

    patched = patched.replace(tail, "", 1)

    # Add a marker near the injected block for idempotence.
    patched = patched.replace(
        "# SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)",
        "# SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)\n" + MARKER.rstrip("\n"),
        1,
    )

    TARGET.write_text(patched, encoding="utf-8")
    print("OK: refined pytest directory invocation gate detection (v2)")


if __name__ == "__main__":
    main()
