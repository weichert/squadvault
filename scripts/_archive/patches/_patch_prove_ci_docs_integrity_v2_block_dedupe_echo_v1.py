from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

OLD_BLOCK = """\
# SV_GATE: docs_integrity (v2) begin
echo "==> Docs integrity gate (v2)"
bash scripts/gate_docs_integrity_v2.sh
# SV_GATE: docs_integrity (v2) end
"""

NEW_BLOCK = """\
# SV_GATE: docs_integrity (v2) begin
bash scripts/gate_docs_integrity_v2.sh
# SV_GATE: docs_integrity (v2) end
"""


def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if NEW_BLOCK in text:
        return

    if OLD_BLOCK not in text:
        raise SystemExit("expected docs_integrity (v2) block not found (refuse to guess)")

    # refuse ambiguity
    if text.count(OLD_BLOCK) != 1:
        raise SystemExit("expected docs_integrity (v2) block to appear exactly once")

    PROVE.write_text(text.replace(OLD_BLOCK, NEW_BLOCK), encoding="utf-8")


if __name__ == "__main__":
    main()
