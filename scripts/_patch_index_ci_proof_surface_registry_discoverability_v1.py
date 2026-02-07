from __future__ import annotations

from pathlib import Path
import sys

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

MARKER = "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->"
BULLET = "- scripts/check_ci_proof_surface_matches_registry_v1.sh — CI Proof Surface Registry Gate (canonical)"

BLOCK = MARKER + "\n" + BULLET + "\n\n"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}") from e


def _write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to write {path}: {e}") from e


def main() -> int:
    if not INDEX.exists():
        print(f"ERROR: missing index file: {INDEX}", file=sys.stderr)
        return 2

    original = _read_text(INDEX)

    # Line-based exact removal (keeps all other content in original order).
    lines = original.splitlines()
    filtered: list[str] = []
    for line in lines:
        if line == MARKER:
            continue
        if line == BULLET:
            continue
        filtered.append(line)

    # Reconstruct with newline termination.
    rebuilt = "\n".join(filtered) + "\n"

    # Append the block exactly once at end (deduped).
    rebuilt = rebuilt + BLOCK

    if rebuilt == original:
        # No diff; keep file untouched.
        return 0

    _write_text(INDEX, rebuilt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
