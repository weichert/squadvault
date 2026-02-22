from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_DISCOVERABILITY_v1_BEGIN -->"
END = "<!-- SV_CREATIVE_SURFACE_REGISTRY_DISCOVERABILITY_v1_END -->"

SINGLE_LINE_MARKER = "<!-- SV_CREATIVE_SURFACE_REGISTRY: v1 -->"
BULLET_LINE = "- docs/80_indices/ops/Creative_Surface_Registry_v1.0.md — Creative Surface Registry (canonical pointers) (v1)"

# Existing duplicate offenders from your grep output
DUP_DOC_SNIPPET = "`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md`"
DUP_PARITY_BULLET = "- scripts/gate_creative_surface_registry_parity_v1.sh — Creative Surface Registry parity gate (v1)"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, s: str) -> bool:
    old = _read(p)
    if old == s:
        return False
    p.write_text(s, encoding="utf-8")
    return True


def _ensure_block(text: str) -> str:
    block = "\n".join([BEGIN, SINGLE_LINE_MARKER, BULLET_LINE, END]) + "\n"

    if (BEGIN in text) != (END in text):
        raise SystemExit("Refusing: discoverability block markers are partial (BEGIN/END mismatch).")

    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        _, post = rest.split(END, 1)
        pre = pre.rstrip("\n") + "\n"
        post = post.lstrip("\n")
        return pre + block + ("\n" + post if post else "")

    # Insert near the existing "**Creative Surface Registry**" section if present; else after first H1.
    lines = text.splitlines(True)
    insert_at = None

    for i, line in enumerate(lines):
        if "Creative Surface Registry" in line and line.strip().startswith("- **"):
            insert_at = i + 1
            break

    if insert_at is None:
        for i, line in enumerate(lines[:120]):
            if line.startswith("# "):
                insert_at = i + 1
                while insert_at < len(lines) and lines[insert_at].strip() == "":
                    insert_at += 1
                break

    if insert_at is None:
        insert_at = 0

    out = "".join(lines[:insert_at]) + ("\n" if insert_at > 0 and not lines[insert_at - 1].endswith("\n\n") else "") + block + "\n" + "".join(lines[insert_at:])
    return out


def _dedupe_exact_line(text: str, line: str) -> str:
    # Keep first occurrence, remove subsequent exact matches.
    out_lines = []
    seen = False
    for ln in text.splitlines(True):
        if ln.rstrip("\n") == line:
            if not seen:
                out_lines.append(ln)
                seen = True
            else:
                # drop duplicate
                continue
        else:
            out_lines.append(ln)
    return "".join(out_lines)


def _dedupe_doc_snippet(text: str) -> str:
    # The backticked doc path currently appears twice; keep at most one occurrence overall,
    # but do NOT touch the bounded discoverability block (which uses the BULLET_LINE).
    out_lines = []
    seen = False
    in_block = False

    for ln in text.splitlines(True):
        if BEGIN in ln:
            in_block = True
        if END in ln:
            # include END line; block ends after this line
            out_lines.append(ln)
            in_block = False
            continue

        if in_block:
            out_lines.append(ln)
            continue

        if DUP_DOC_SNIPPET in ln:
            if not seen:
                out_lines.append(ln)
                seen = True
            else:
                continue
        else:
            out_lines.append(ln)

    return "".join(out_lines)


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"Refusing: missing {INDEX}")

    text = _read(INDEX)
    text = _ensure_block(text)

    # Dedupes based on your observed duplicates
    text = _dedupe_doc_snippet(text)
    text = _dedupe_exact_line(text, DUP_PARITY_BULLET)

    _write_if_changed(INDEX, text)


if __name__ == "__main__":
    main()
