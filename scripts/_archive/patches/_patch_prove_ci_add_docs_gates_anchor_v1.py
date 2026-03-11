from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# === SV_ANCHOR: docs_gates (v1) ==="
END = "# === /SV_ANCHOR: docs_gates (v1) ==="

ANCHOR_BLOCK = """\
# === SV_ANCHOR: docs_gates (v1) ===
# Patch insertion point for doc/index gates.
# Patcher rule: insert additional doc/index gates immediately BELOW this block.
# === /SV_ANCHOR: docs_gates (v1) ===

"""

NEEDLE = "bash scripts/prove_docs_integrity_v1.sh"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def _extract_bounded(text: str) -> str | None:
    b = text.find(BEGIN)
    if b == -1:
        return None
    e = text.find(END, b)
    if e == -1:
        _refuse(f"found BEGIN anchor but missing END anchor: {END}")
    e = e + len(END)
    # include trailing newline if present
    if e < len(text) and text[e : e + 1] == "\n":
        e += 1
    return text[b:e]


def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing required file: {PROVE}")

    s = _read(PROVE)

    bounded = _extract_bounded(s)
    if bounded is not None:
        # Anchor exists; ensure it matches the canonical block (allow optional trailing newline)
        expected = ANCHOR_BLOCK.strip("\n")
        got = bounded.strip("\n")
        if got != expected:
            _refuse(f"{PROVE}: docs_gates anchor exists but does not match canonical contents.")
        return

    if NEEDLE not in s:
        _refuse(f"could not find insertion needle: {NEEDLE}")

    # Insert immediately before the first docs integrity invocation.
    out = s.replace(NEEDLE, ANCHOR_BLOCK + NEEDLE, 1)
    _write(PROVE, out)


if __name__ == "__main__":
    main()
