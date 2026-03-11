from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/contracts/creative_sharepack_output_contract_v1.md")

GATE_PATH = "scripts/gate_creative_surface_fingerprint_canonical_v1.sh"

BEGIN = "<!-- SV_ENFORCED_BY_CREATIVE_SURFACE_FINGERPRINT_CANONICAL_GATE_v1_BEGIN -->"
END = "<!-- SV_ENFORCED_BY_CREATIVE_SURFACE_FINGERPRINT_CANONICAL_GATE_v1_END -->"

ENTRY = (
    f"{BEGIN}\n"
    f"- `{GATE_PATH}` — Enforce creative surface fingerprint artifact canonical (v1)\n"
    f"{END}\n"
)

HEADER = "## Enforced By"

def main() -> None:
    src = TARGET.read_text(encoding="utf-8")

    if GATE_PATH in src:
        print("OK: contract already links creative surface fingerprint canonical gate under Enforced By (noop).")
        return

    if HEADER not in src:
        raise SystemExit("REFUSE: could not find '## Enforced By' in target contract doc.")

    hi = src.index(HEADER)
    line_end = src.find("\n", hi)
    if line_end == -1:
        raise SystemExit("REFUSE: unexpected contract doc shape (no newline after header).")

    insert_at = line_end + 1
    prefix = src[:insert_at]
    suffix = src[insert_at:]

    entry_text = ENTRY if suffix.startswith("\n") else ("\n" + ENTRY)
    out = prefix + entry_text + suffix

    CANONICAL = out  # canonical rewrite sentinel
    if CANONICAL == src:
        print("OK: contract patch produced identical content (noop).")
        return

    TARGET.write_text(CANONICAL, encoding="utf-8")
    print("OK: patched contract Enforced By (added creative surface fingerprint canonical gate).")

if __name__ == "__main__":
    main()
