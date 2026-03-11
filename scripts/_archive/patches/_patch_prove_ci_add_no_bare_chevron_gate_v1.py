from __future__ import annotations

from pathlib import Path
import subprocess
import sys


TARGET = Path("scripts/prove_ci.sh")


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, text: str) -> bool:
    if p.exists() and _read(p) == text:
        return False
    p.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    root = _repo_root()
    path = root / TARGET
    if not path.exists():
        print(f"FATAL: missing {TARGET}", file=sys.stderr)
        return 2

    s = _read(path)
    call = "bash scripts/gate_no_bare_chevron_markers_v1.sh"
    if call in s:
        print("OK: no changes needed.")
        return 0

    insertion = '\necho "==> No-bare-chevron markers gate"\n' + call + "\n"

    # Anchor: after the bash -n check banner if present
    anchor = "=== Check: bash -n on scripts/*.sh ==="
    if anchor in s:
        s = s.replace(anchor, anchor + insertion, 1)
    else:
        # Fallback: after suite header
        hdr = "== CI Proof Suite =="
        if hdr in s:
            s = s.replace(hdr, hdr + insertion, 1)
        else:
            print("FATAL: could not find insertion anchor in prove_ci.sh", file=sys.stderr)
            return 3

    changed = _write_if_changed(path, s)
    print("OK: patch applied." if changed else "OK: no changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
