from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
NEEDED = "docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md"

MARK = "ci_guardrails_index_add_docs_integrity_link_v1"

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not INDEX.exists():
        die(f"FAIL: missing index file: {INDEX}")
    if not Path(NEEDED).exists():
        die(f"FAIL: missing invariant doc: {NEEDED}")

    s = INDEX.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    if NEEDED in s:
        print("NO-OP: CI guardrails index already references docs integrity invariant")
        return

    # Append as a new bullet under a reasonable section if one exists; otherwise append at end.
    lines = s.splitlines()

    insert_at = len(lines)
    # Prefer inserting under a "Docs" / "Documentation" / "Integrity" heading if present.
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low in ("## docs", "## documentation", "## integrity", "## docs integrity", "## guardrails"):
            insert_at = i + 1
            # skip any immediate blank lines after heading
            while insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            break

    bullet = f"- `{NEEDED}`  <!-- {MARK} -->"

    out_lines = lines[:insert_at]
    if insert_at == len(lines) and (len(out_lines) > 0 and out_lines[-1].strip() != ""):
        out_lines.append("")  # keep file readable

    out_lines.append(bullet)
    out_lines.extend(lines[insert_at:])

    out = "\n".join(out_lines).rstrip() + "\n"
    INDEX.write_text(out, encoding="utf-8", newline="\n")
    print(f"OK: added CI guardrails index reference -> {NEEDED}")

if __name__ == "__main__":
    main()
