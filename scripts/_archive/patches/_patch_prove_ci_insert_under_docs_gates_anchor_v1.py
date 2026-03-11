from __future__ import annotations

from pathlib import Path

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

def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing required file: {PROVE}")

    gate_path = (Path("scripts") / Path((__import__("os").environ.get("SV_DOCS_GATES_INSERT_PATH", "")).strip())).as_posix()
    gate_label = (__import__("os").environ.get("SV_DOCS_GATES_INSERT_LABEL", "")).strip()

    if not gate_path or not gate_label:
        _refuse(
            "missing required env vars: SV_DOCS_GATES_INSERT_LABEL and/or SV_DOCS_GATES_INSERT_PATH\n"
            "Example:\n"
            "  SV_DOCS_GATES_INSERT_LABEL='CI Guardrails ops entrypoints section + TOC (v2)'\n"
            "  SV_DOCS_GATES_INSERT_PATH='scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh'\n"
        )

    # Canonical inserted block (ECHO SAFE)
    insert_block = (
        f'echo "==> Gate: {gate_label}"\n'
        f"bash {gate_path}\n"
        "\n"
    )

    s = _read(PROVE)

    if ANCHOR_BEGIN not in s or ANCHOR_END not in s:
        _refuse("missing docs_gates anchor markers in scripts/prove_ci.sh (expected v1 anchor)")

    # Idempotent: if the bash invocation already exists anywhere, do nothing.
    # (We intentionally avoid “move/relocate” semantics here; that’s a separate patch.)
    if f"bash {gate_path}\n" in s:
        return

    a0 = s.find(ANCHOR_BEGIN)
    a1 = s.find(ANCHOR_END, a0)
    if a1 == -1:
        _refuse(f"found anchor begin but missing anchor end: {ANCHOR_END}")

    a1_end = a1 + len(ANCHOR_END)
    # include trailing newline after anchor end line if present
    if a1_end < len(s) and s[a1_end : a1_end + 1] == "\n":
        a1_end += 1

    out = s[:a1_end] + insert_block + s[a1_end:]
    _write(PROVE, out)

if __name__ == "__main__":
    main()
