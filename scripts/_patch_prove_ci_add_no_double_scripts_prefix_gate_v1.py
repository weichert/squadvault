from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

LABEL = "no double scripts prefix (v1)"
PATH = "scripts/gate_no_double_scripts_prefix_v1.sh"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing required file: {PROVE}")

    s = _read(PROVE)
    if f"bash {PATH}\n" in s:
        return

    # We intentionally delegate the insertion mechanics to the v2 insertion patcher/wrapper.
    _refuse(
        "This patcher is a guardrail stub and must be applied via its wrapper, which calls "
        "patch_prove_ci_insert_under_docs_gates_anchor_v2.sh with the correct env vars."
    )


if __name__ == "__main__":
    main()
