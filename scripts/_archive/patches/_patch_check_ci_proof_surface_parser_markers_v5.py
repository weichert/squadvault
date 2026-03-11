from __future__ import annotations

from pathlib import Path
import re

CHECK = Path("scripts/check_ci_proof_surface_matches_registry_v1.sh")

def main() -> None:
    if not CHECK.exists():
        raise SystemExit(f"ERROR: missing {CHECK}")

    text = CHECK.read_text(encoding="utf-8")

    # Idempotence: if we already use input redirection for registry loop, no-op.
    if re.search(r'while\s+IFS=\s*read\s+-r\s+line;.*\n.*done\s*<\s*"\$\{?registry\}?\"', text, flags=re.S):
        print("OK: registry while-loop already uses input redirection (v5 idempotent).")
        return

    # Find a cat-pipe-while loop that consumes $registry
    # Accept both: cat "${registry}" | while ... and cat "$registry" | while ...
    m = re.search(
        r'(cat\s+"?\$\{?registry\}?"?\s*\|\s*while\s+IFS=\s*read\s+-r\s+line;\s*do)(?P<body>.*?)(\n\s*done\s*)',
        text,
        flags=re.S,
    )
    if not m:
        raise SystemExit(
            "ERROR: could not find 'cat $registry | while IFS= read -r line; do' pattern to de-subshell.\n"
            "Open scripts/check_ci_proof_surface_matches_registry_v1.sh and look for a piped while loop."
        )

    prefix = m.group(1)
    body = m.group("body")
    # Replace with: while ...; do ... done < "$registry"
    replacement = f'while IFS= read -r line; do{body}\n  done < "${{registry}}"\n'

    # Replace the entire matched construct from 'cat ... | while ... do' through 'done'
    # We need to capture the exact 'done' line too; do a broader match for safety:
    m2 = re.search(
        r'cat\s+"?\$\{?registry\}?"?\s*\|\s*while\s+IFS=\s*read\s+-r\s+line;\s*do(?P<body>.*?\n)\s*done\s*',
        text,
        flags=re.S,
    )
    if not m2:
        raise SystemExit("ERROR: internal: broader match failed (unexpected).")

    new_text = text[:m2.start()] + replacement + text[m2.end():]
    CHECK.write_text(new_text, encoding="utf-8")
    print("OK: converted piped while-loop to input-redirection loop (v5).")

if __name__ == "__main__":
    main()
