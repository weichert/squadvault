from __future__ import annotations

from pathlib import Path
import re


TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")


def _read(path: Path) -> str:
    """Read UTF-8 text with a clear fail-fast if missing."""
    if not path.exists():
        raise SystemExit(f"missing: {path}")
    return path.read_text(encoding="utf-8")


def _write(path: Path, txt: str) -> None:
    """Write UTF-8 text with exactly one trailing newline."""
    path.write_text(txt.rstrip() + "\n", encoding="utf-8")


def _transform(txt: str) -> str:
    """
    PURPOSE:
      Demonstrate a safe, readable, idempotent patcher shape.

    GUARANTEES:
      - idempotent: rerunning produces no further changes
      - stable output: no nondeterministic data
      - single trailing newline
      - conservative whitespace normalization only
    """
    out = txt

    # Collapse 4+ blank lines to max 3 (very conservative).
    out = re.sub(r"\n{4,}", "\n\n\n", out)

    return out


def main() -> None:
    original = _read(TARGET)
    updated = _transform(original)

    if updated == original:
        return  # no-op is success (idempotent)

    _write(TARGET, updated)


if __name__ == "__main__":
    main()
