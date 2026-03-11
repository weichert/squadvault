from __future__ import annotations

from pathlib import Path
import os

PROVE = Path("scripts/prove_ci.sh")

ANCHOR_BEGIN = "# === SV_ANCHOR: docs_gates (v1) ==="
ANCHOR_END = "# === /SV_ANCHOR: docs_gates (v1) ==="


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def _normalize_gate_path(raw: str) -> str:
    p = raw.strip()
    if not p:
        _refuse("empty SV_DOCS_GATES_INSERT_PATH")

    # Normalize leading "./"
    if p.startswith("./"):
        p = p[2:]

    # Refuse dangerous forms
    if p.startswith("/"):
        _refuse("SV_DOCS_GATES_INSERT_PATH must be repo-relative (refuse absolute paths)")
    if ".." in p.split("/"):
        _refuse("SV_DOCS_GATES_INSERT_PATH must not contain '..'")

    # If user gave scripts/... keep it; else allow bare filename only.
    if p.startswith("scripts/"):
        return p

    if "/" in p:
        _refuse(
            "SV_DOCS_GATES_INSERT_PATH must be either:\n"
            "  - scripts/<gate>.sh\n"
            "  - ./scripts/<gate>.sh\n"
            "  - <gate>.sh (bare filename)\n"
            f"Got: {raw!r}"
        )

    return f"scripts/{p}"


def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing required file: {PROVE}")

    gate_label = os.environ.get("SV_DOCS_GATES_INSERT_LABEL", "").strip()
    gate_path_raw = os.environ.get("SV_DOCS_GATES_INSERT_PATH", "").strip()

    if not gate_label or not gate_path_raw:
        _refuse(
            "missing required env vars: SV_DOCS_GATES_INSERT_LABEL and/or SV_DOCS_GATES_INSERT_PATH\n"
            "Example:\n"
            "  SV_DOCS_GATES_INSERT_LABEL='CI Guardrails ops entrypoints section + TOC (v2)'\n"
            "  SV_DOCS_GATES_INSERT_PATH='scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh'\n"
        )

    gate_path = _normalize_gate_path(gate_path_raw)
    gate_basename = gate_path.split("/")[-1]

    insert_block = (
        f'echo "==> Gate: {gate_label}"\n'
        f"bash {gate_path}\n"
        "\n"
    )

    s = _read(PROVE)

    if ANCHOR_BEGIN not in s or ANCHOR_END not in s:
        _refuse("missing docs_gates anchor markers in scripts/prove_ci.sh (expected v1 anchor)")

    # Strong idempotency:
    # 1) exact bash line exists
    if f"bash {gate_path}\n" in s:
        return

    # 2) also avoid duplicates by basename (defensive)
    if gate_basename in s:
        return

    a0 = s.find(ANCHOR_BEGIN)
    a1 = s.find(ANCHOR_END, a0)
    if a1 == -1:
        _refuse(f"found anchor begin but missing anchor end: {ANCHOR_END}")

    a1_end = a1 + len(ANCHOR_END)
    if a1_end < len(s) and s[a1_end : a1_end + 1] == "\n":
        a1_end += 1

    out = s[:a1_end] + insert_block + s[a1_end:]
    _write(PROVE, out)


if __name__ == "__main__":
    main()
