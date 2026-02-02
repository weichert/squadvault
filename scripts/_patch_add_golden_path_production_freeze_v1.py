from __future__ import annotations

from pathlib import Path


TARGET = Path("docs/canonical/Golden_Path_Production_Freeze_v1.0.md")

CONTENT = """\
# Golden Path — Production Freeze (v1.0)

Status: FROZEN — PRODUCTION-GRADE

As of commit:
- HEAD: 66601c9
- CI: clean
- Determinism gates: enforced
- Golden Path proof: passing

This freeze certifies the Golden Path as:
- deterministic
- auditable
- safe for ongoing feature development

Changes to Golden Path behavior require:
- a new versioned patcher
- explicit freeze supersession

Date: 2026-02-01
"""


def main() -> None:
    if TARGET.exists():
        raise SystemExit(f"ERROR: target already exists (refusing to overwrite): {TARGET}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(CONTENT, encoding="utf-8")
    print(f"OK: created {TARGET}")


if __name__ == "__main__":
    main()
