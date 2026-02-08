from __future__ import annotations

from pathlib import Path

ALLOW = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")

WRAPPER = "scripts/patch_add_gate_ops_indices_no_autofill_placeholders_v1.sh"
MARKER = "# SV_ALLOWLIST: add_gate_ops_indices_no_autofill_placeholders (v1)"

def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing {ALLOW}")

    text = ALLOW.read_text(encoding="utf-8")

    if MARKER in text:
        if WRAPPER in text:
            print("OK: wrapper already allowlisted (v1)")
            return
        raise SystemExit("ERROR: marker exists but wrapper missing; refuse ambiguous state")

    block = f'{MARKER}\n  "{WRAPPER}"\n\n'

    if "EOF" in text:
        idx = text.rfind("EOF")
        new_text = text[:idx] + block + text[idx:]
    else:
        new_text = text.rstrip() + "\n\n" + block

    ALLOW.write_text(new_text, encoding="utf-8")
    print("UPDATED:", ALLOW)

if __name__ == "__main__":
    main()
