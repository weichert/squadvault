from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
MARKER = "SV_PATCH_GP_GUARD_SELECTION_FINGERPRINT_V1"


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    # Insert right after the line that prints "Selected assembly: ..."
    # (this exists in your logs as: Selected assembly: /path/to/file.md)
    hit = None
    for i, line in enumerate(lines):
        if "Selected assembly:" in line and ("echo" in line):
            hit = i
            break

    if hit is None:
        raise SystemExit(
            "ERROR: could not find an 'echo' line containing 'Selected assembly:' in scripts/prove_golden_path.sh.\n"
            "Open scripts/prove_golden_path.sh and search for the Selected assembly echo; adjust this patcher if needed."
        )

    snippet = (
        "\n"
        f"# {MARKER}\n"
        "# Guardrail: exported assembly must include a real 64-lower-hex selection fingerprint.\n"
        "# This prevents regressions where exports accidentally embed placeholder 'test-fingerprint'.\n"
        'if grep -q -- "Selection fingerprint: test-fingerprint" "$ASSEMBLY"; then\n'
        '  echo "ERROR: export contains placeholder Selection fingerprint: test-fingerprint" >&2\n'
        "  exit 1\n"
        "fi\n"
        'if ! grep -Eq -- "^Selection fingerprint: [0-9a-f]{64}$" "$ASSEMBLY"; then\n'
        '  echo "ERROR: export missing real 64-hex Selection fingerprint line" >&2\n'
        '  echo "== fingerprint lines (debug) ==" >&2\n'
        '  grep -n -- "Selection fingerprint:" "$ASSEMBLY" >&2 || true\n'
        "  exit 1\n"
        "fi\n"
    )

    lines.insert(hit + 1, snippet)

    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"OK: patched {TARGET} ({MARKER}).")


if __name__ == "__main__":
    main()
