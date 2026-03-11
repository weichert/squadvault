from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END = "<!-- CI_PROOF_RUNNERS_END -->"

ITEM_PATH = "scripts/prove_creative_determinism_v1.sh"
ITEM_LINE = f"- {ITEM_PATH} — Prove: creative determinism drift guard (v1)\n"

def main() -> None:
    if not REG.exists():
        raise SystemExit(f"Missing registry doc: {REG}")

    txt = REG.read_text(encoding="utf-8")
    if BEGIN not in txt:
        raise SystemExit(f"Refusing: missing marker {BEGIN}")
    if END not in txt:
        raise SystemExit(f"Refusing: missing marker {END}")

    pre, rest = txt.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = mid.splitlines(keepends=True)

    # Idempotent no-op if already present anywhere inside the block.
    for ln in lines:
        core = ln.strip()
        if core.startswith("-") and ITEM_PATH in core:
            return

    bullets: list[tuple[str, int]] = []
    for i, ln in enumerate(lines):
        core = ln.strip()
        if core.startswith("- "):
            token = core[2:].split()[0]
            bullets.append((token, i))

    if not bullets:
        new_mid = "".join([ITEM_LINE] + lines)
        REG.write_text(pre + BEGIN + new_mid + END + post, encoding="utf-8")
        return

    bullets_sorted = sorted(bullets, key=lambda t: t[0])
    insert_idx: int | None = None
    for token, idx in bullets_sorted:
        if ITEM_PATH < token:
            insert_idx = idx
            break

    if insert_idx is None:
        last_idx = max(i for _, i in bullets)
        new_lines = lines[: last_idx + 1] + [ITEM_LINE] + lines[last_idx + 1 :]
    else:
        new_lines = lines[:insert_idx] + [ITEM_LINE] + lines[insert_idx:]

    REG.write_text(pre + BEGIN + "".join(new_lines) + END + post, encoding="utf-8")

if __name__ == "__main__":
    main()
