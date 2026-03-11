from __future__ import annotations

from pathlib import Path
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel: str, content: str) -> None:
    root = _repo_root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel} (exit {proc.returncode}).")


def main() -> int:
    root = _repo_root()
    wrapper = root / "scripts" / "patch_docs_fill_ci_guardrails_autofill_descriptions_v1.sh"
    if not wrapper.exists():
        raise SystemExit("ERROR: wrapper not found: scripts/patch_docs_fill_ci_guardrails_autofill_descriptions_v1.sh")

    s = _read(wrapper)
    guard = (
        '\n'
        '# SV_IDEMPOTENCE_MODE guard: allowlisted wrappers must be NOOP\n'
        'if [ "${SV_IDEMPOTENCE_MODE:-0}" = "1" ]; then\n'
        '  echo "OK: idempotence mode: skipping CI guardrails autofill descriptions patch (v1)"\n'
        '  exit 0\n'
        'fi\n'
    )

    if "SV_IDEMPOTENCE_MODE" in s:
        print("OK: wrapper already guarded for SV_IDEMPOTENCE_MODE (noop).")
        return 0

    # Insert after strict mode line if present, else at top after shebang.
    lines = s.splitlines(True)
    insert_at = None
    for i, ln in enumerate(lines):
        if "set -euo pipefail" in ln:
            insert_at = i + 1
            break
    if insert_at is None:
        # after shebang
        for i, ln in enumerate(lines):
            if ln.startswith("#!"):
                insert_at = i + 1
                break
        if insert_at is None:
            insert_at = 0

    lines.insert(insert_at, guard)
    out = "".join(lines)
    _clipwrite("scripts/patch_docs_fill_ci_guardrails_autofill_descriptions_v1.sh", out)
    print("OK: added SV_IDEMPOTENCE_MODE=1 NOOP guard to autofill wrapper (v1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
