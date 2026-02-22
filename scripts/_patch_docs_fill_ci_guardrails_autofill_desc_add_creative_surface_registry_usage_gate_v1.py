from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "scripts" / "_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py"

NEW_KEY = "scripts/gate_creative_surface_registry_usage_v1.sh"
NEW_VAL = "CI guardrails gate: enforce Creative Surface registry usage (v1)"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, s: str) -> bool:
    old = _read(p)
    if old == s:
        return False
    p.write_text(s, encoding="utf-8")
    return True


def _find_best_brace_block(src: str) -> tuple[int, int]:
    # Find all balanced { ... } blocks and score by how many times they contain "scripts/".
    # Choose the highest score; tie-breaker: longest span.
    stack: list[int] = []
    blocks: list[tuple[int, int, int]] = []  # (score, start, end)

    for i, ch in enumerate(src):
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if not stack:
                continue
            start = stack.pop()
            end = i + 1
            chunk = src[start:end]
            score = chunk.count("scripts/")
            # only consider plausible candidates
            if score >= 5:
                blocks.append((score, start, end))

    if not blocks:
        raise SystemExit("ERROR: could not locate any { } block containing enough 'scripts/' entries")

    # Prefer highest scripts/ density, then longest span
    blocks.sort(key=lambda t: (t[0], t[2] - t[1]), reverse=True)
    _, start, end = blocks[0]
    return start, end


def _infer_entry_indent(block: str) -> str:
    # Prefer indentation used by existing entries:
    # look at last non-empty line before the closing brace.
    lines = block.splitlines()
    for line in reversed(lines[:-1]):  # exclude the closing brace line itself
        if line.strip():
            return line[: len(line) - len(line.lstrip())]
    # fallback: 4 spaces
    return "    "


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: target missing: {TARGET.as_posix()}")

    src = _read(TARGET)

    if NEW_KEY in src:
        print("NOOP: mapping already present")
        return

    start, end = _find_best_brace_block(src)
    block = src[start:end]

    indent = _infer_entry_indent(block)
    entry = f'{indent}"{NEW_KEY}": "{NEW_VAL}",\n'

    # Insert right before the final '}' of the selected block
    insert_at = end - 1
    new = src[:insert_at] + entry + src[insert_at:]

    if new == src:
        print("NOOP: already canonical")
        return

    _write_if_changed(TARGET, new)
    print(f"OK: inserted desc mapping into brace block in {TARGET.as_posix()}")


if __name__ == "__main__":
    main()
