from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")
SENTINEL = "SV_PATCH: fix safe_grep invocation signature (drop leading -I) (v2)"

# Transform:
#   safe_grep -I VAR grep <args...>
# into:
#   safe_grep VAR grep -I <args...>
PAT = re.compile(
    r"^(?P<indent>\s*)safe_grep\s+-I\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+grep(?P<space>\s+)",
    re.M,
)

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if SENTINEL in txt:
        print("OK: target already patched for safe_grep signature (v2)")
        return

    def repl(m: re.Match[str]) -> str:
        return f"{m.group('indent')}safe_grep {m.group('var')} grep{m.group('space')}-I "

    new_txt, n = PAT.subn(repl, txt)

    if n == 0:
        die("refusing to patch: no 'safe_grep -I VAR grep ...' patterns found")

    # Add sentinel after shebang
    lines = new_txt.splitlines(True)
    out: list[str] = []
    inserted = False
    for i, ln in enumerate(lines):
        out.append(ln)
        if not inserted and i == 0 and ln.startswith("#!"):
            out.append("\n")
            out.append(f"# {SENTINEL}\n")
            out.append("# safe_grep signature is: safe_grep VAR_NAME <command...>\n")
            out.append("# Do not pass '-I' as VAR_NAME; move it into grep args.\n")
            out.append("# /SV_PATCH\n\n")
            inserted = True

    TARGET.write_text("".join(out), encoding="utf-8")
    print(f"OK: fixed {n} safe_grep invocation(s) to keep VAR_NAME first")

if __name__ == "__main__":
    main()
