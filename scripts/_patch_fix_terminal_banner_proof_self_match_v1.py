from __future__ import annotations

from pathlib import Path

PROOF = Path("scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh")
PATCHER_V3 = Path("scripts/_patch_prove_terminal_banner_gate_behavior_and_ci_hint_v3.py")

def patch_proof_script() -> None:
    if not PROOF.exists():
        raise SystemExit(f"ERROR: missing proof script: {PROOF}")

    text = PROOF.read_text(encoding="utf-8")

    # If we've already converted case-1 generation to printf, we're done.
    if 'printf' in text and 'Last"" login:' in text:
        print("OK: proof script already avoids start-of-line banner literals (idempotent).")
        return

    # Replace the heredoc that starts with a banner line with a printf that constructs it
    # without placing "Last" + " login:" at start-of-line in this tracked file.
    old = """cat > "${TMP}" <<'EOF'
Last" + " login: Fri Feb  6 23:41:20 on ttys061
EOF
"""
    new = """# Generate a real banner line in the temp file without embedding it at start-of-line in this script.
printf '%s\\n' "Last"" login: Fri Feb  6 23:41:20 on ttys061" > "${TMP}"
"""

    if old not in text:
        # Fallback: try a looser replacement if spacing drifted.
        if 'Last" + " login:' not in text:
            raise SystemExit("ERROR: expected banner-line case not found in proof script; refusing to patch.")
        # Best-effort: replace the first occurrence of a line that begins with Last" + " login:
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        replaced = False
        i = 0
        while i < len(lines):
            if (not replaced) and lines[i].startswith('cat > "${TMP}"') and i + 2 < len(lines) and "Last" + " login:" in lines[i+1]:
                # Replace the 3-line heredoc header + banner + EOF
                out.append(new)
                # skip until after EOF line
                i += 1
                while i < len(lines) and "EOF" not in lines[i]:
                    i += 1
                if i < len(lines):
                    i += 1
                replaced = True
                continue
            out.append(lines[i])
            i += 1
        if not replaced:
            raise SystemExit("ERROR: could not locate the banner heredoc block reliably; refusing to patch.")
        text2 = "".join(out)
    else:
        text2 = text.replace(old, new, 1)

    PROOF.write_text(text2, encoding="utf-8")
    print("OK: patched proof script to avoid start-of-line banner literals.")

def patch_patcher_v3_proof_text() -> None:
    if not PATCHER_V3.exists():
        raise SystemExit(f"ERROR: missing patcher v3: {PATCHER_V3}")

    text = PATCHER_V3.read_text(encoding="utf-8")

    # If already fixed, do nothing.
    if 'Last"" login:' in text:
        print("OK: patcher v3 already avoids start-of-line banner literals (idempotent).")
        return

    # Replace the exact heredoc snippet inside PROOF_TEXT.
    old = """cat > "${TMP}" <<'EOF'
Last" + " login: Fri Feb  6 23:41:20 on ttys061
EOF
"""
    new = """# Generate a real banner line in the temp file without embedding it at start-of-line in this tracked file.
printf '%s\\n' "Last"" login: Fri Feb  6 23:41:20 on ttys061" > "${TMP}"
"""

    if old not in text:
        # If it drifted, refuse — we don't want to risk corrupting the patcher.
        raise SystemExit("ERROR: could not find expected heredoc block in patcher v3 PROOF_TEXT; refusing to patch.")

    PATCHER_V3.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("OK: patched patcher v3 PROOF_TEXT to avoid start-of-line banner literals.")

def main() -> None:
    patch_proof_script()
    patch_patcher_v3_proof_text()

if __name__ == "__main__":
    main()
