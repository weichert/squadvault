from __future__ import annotations

from pathlib import Path
import re

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
PROVE = Path("scripts/prove_ci.sh")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

# Stable placeholder. Humans can refine later without breaking parity.
DESC = "— (autofill) describe gate purpose"

GATE_RE = re.compile(r"^[ \t]*bash[ \t]+(scripts/gate_[^\s]+\.sh)(?:[ \t]|$)")

BULLET_RE = re.compile(r"^[ \t]*-[ \t]*(scripts/[^\s]+)")

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"ERROR: missing {INDEX}")
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = INDEX.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: bounded entrypoints markers missing in ops index; refuse")

    pre, rest = text.split(BEGIN, 1)
    bounded, post = rest.split(END, 1)

    # Collect currently indexed entrypoints from bullets
    indexed: set[str] = set()
    for line in bounded.splitlines():
        m = BULLET_RE.match(line)
        if m:
            indexed.add(m.group(1).strip())

    # Collect executed gate entrypoints from prove_ci (static surface)
    executed: set[str] = set()
    for line in PROVE.read_text(encoding="utf-8").splitlines():
        m = GATE_RE.match(line)
        if m:
            executed.add(m.group(1).strip())

    missing = sorted(executed - indexed)

    if not missing:
        print("OK: no missing executed gate entrypoints to index")
        return

    # Append missing bullets at the end of bounded section, before END.
    # Keep bounded section formatting stable: ensure it ends with a newline.
    bounded_out = bounded.rstrip("\n") + "\n"
    for path in missing:
        bounded_out += f"- {path} {DESC}\n"

    new_text = pre + BEGIN + bounded_out + END + post
    INDEX.write_text(new_text, encoding="utf-8")

    print("UPDATED:", INDEX)
    print("Added:")
    for p in missing:
        print("  -", p)

if __name__ == "__main__":
    main()
