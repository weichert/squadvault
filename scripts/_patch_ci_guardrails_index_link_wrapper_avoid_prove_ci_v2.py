from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_ci_guardrails_index_add_docs_integrity_link_v1.sh")

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not TARGET.exists():
        die(f"FAIL: missing target wrapper: {TARGET}")

    s = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    if "wrapper_avoid_prove_ci_cleanliness_trap_v2" in s:
        print("NO-OP: already patched (wrapper_avoid_prove_ci_cleanliness_trap_v2)")
        return

    # Remove the prove_ci block and replace with instruction.
    needle = '\necho "==> full prove"\nbash scripts/prove_ci.sh\n'
    if needle not in s:
        die("FAIL: could not find expected prove_ci invocation block to replace")

    replacement = (
        '\n# wrapper_avoid_prove_ci_cleanliness_trap_v2: do not run prove_ci from a dirty repo\n'
        'echo "OK: docs integrity proof passed."\n'
        'echo "Next: git add + commit + push, then run: bash scripts/prove_ci.sh"\n'
    )

    s2 = s.replace(needle, replacement, 1)
    TARGET.write_text(s2, encoding="utf-8", newline="\n")
    print("OK: patched wrapper to avoid prove_ci cleanliness trap (v2)")

if __name__ == "__main__":
    main()
