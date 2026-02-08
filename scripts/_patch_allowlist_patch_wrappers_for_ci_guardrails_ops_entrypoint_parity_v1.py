from __future__ import annotations

from pathlib import Path

ALLOW = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")

WRAPPERS = [
    "scripts/patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "scripts/patch_wire_ci_guardrails_ops_entrypoint_parity_gate_into_prove_ci_v1.sh",
    "scripts/patch_index_ci_guardrails_ops_entrypoint_parity_gate_discoverability_v1.sh",
]

MARKER = "# SV_ALLOWLIST: ci_guardrails_ops_entrypoint_parity (v1)"

def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing {ALLOW}")

    text = ALLOW.read_text(encoding="utf-8")

    # Fail-closed: refuse if file structure doesn't look like shell
    if not text.startswith("#!") and "ALLOWLIST" not in text and "allowlist" not in text:
        raise SystemExit(f"ERROR: {ALLOW} content not recognized; refuse to patch")

    if MARKER in text:
        # already patched
        ok = True
        for w in WRAPPERS:
            if w not in text:
                ok = False
        if ok:
            print("OK: allowlist already contains wrappers")
            return
        raise SystemExit("ERROR: marker exists but wrappers missing; refuse ambiguous state")

    block_lines = [MARKER] + [f'  "{w}"' for w in WRAPPERS] + [""]
    block = "\n".join(block_lines)

    # Heuristic insertion:
    # Insert before the final "EOF" (if heredoc), else append near end.
    if "EOF" in text:
        idx = text.rfind("EOF")
        new_text = text[:idx] + block + text[idx:]
    else:
        new_text = text.rstrip() + "\n\n" + block

    ALLOW.write_text(new_text, encoding="utf-8")
    print("UPDATED: allowlisted new patch wrappers in", ALLOW)

if __name__ == "__main__":
    main()
