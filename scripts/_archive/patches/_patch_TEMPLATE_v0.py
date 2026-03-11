from __future__ import annotations

from pathlib import Path
import re


# -----------------------------------------------------------------------------
# TEMPLATE PATCHER (COPY/RENAME ME)
#
# Usage:
#   1) Copy/rename to: scripts/_patch_<real_name>_vN.py
#   2) Set TARGET to the real file you intend to modify
#   3) Implement _transform() as an idempotent transformation
#
# Invariants we want in every patcher:
#   - idempotent (running twice produces the same output)
#   - stable output (no timestamps, random IDs, etc.)
#   - single trailing newline
#   - minimal, conservative whitespace normalization
# -----------------------------------------------------------------------------


TARGET = Path("PATH/TO/TARGET.md")


def _fail_if_template_target() -> None:
    """
    Fail fast if the user forgot to set TARGET.

    This prevents confusing errors like:
      missing: PATH/TO/TARGET.md
    """
    if str(TARGET) == "PATH/TO/TARGET.md":
        raise SystemExit(
            "Template patcher: set TARGET to a real path before running "
            "(e.g. docs/.../Some_File_v1.0.md)."
        )


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
      <one sentence describing what this patch changes>

    GUARANTEES:
      - idempotent: rerunning produces no further changes
      - stable output: no nondeterministic data
      - single trailing newline
      - conservative whitespace normalization only
    """
    out = txt

    # Example: collapse 4+ blank lines to max 3 (very conservative).
    out = re.sub(r"\n{4,}", "\n\n\n", out)

    return out


def main() -> None:
    _fail_if_template_target()

    original = _read(TARGET)
    updated = _transform(original)

    if updated == original:
        return  # no-op is success (idempotent)

    _write(TARGET, updated)


if __name__ == "__main__":
    main()
