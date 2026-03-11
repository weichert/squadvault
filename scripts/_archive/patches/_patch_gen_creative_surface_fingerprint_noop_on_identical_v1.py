from __future__ import annotations

import sys
from pathlib import Path


TARGET = Path("scripts/gen_creative_surface_fingerprint_v1.py")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    old = TARGET.read_text(encoding="utf-8")
    if "CREATIVE_SURFACE_FINGERPRINT_v1.json" not in old:
        die("unexpected generator shape: missing fingerprint filename token")

    # Canonical generator rewrite:
    # - Preserve schema keys by starting from existing artifact JSON (if present).
    # - Only update keys that already exist (no new schema keys introduced).
    # - Deterministic: git ls-files sorted, json indent=2 sort_keys=True trailing newline.
    canonical = """\
from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUT = Path("artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json")


def _git_ls_files() -> list[str]:
    p = subprocess.run(
        ["git", "ls-files"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    files = [line.strip() for line in p.stdout.splitlines() if line.strip()]
    files.sort()
    return files


def _read_prev_payload() -> dict:
    if not OUT.exists():
        return {}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        # If artifact is malformed, fall back to empty to avoid crashing generator.
        return {}


def main() -> None:
    files = _git_ls_files()
    files_n = len(files)

    payload = _read_prev_payload()

    # Preserve schema keys: only mutate keys that already exist.
    if "files" in payload:
        payload["files"] = files
    if "files_n" in payload:
        payload["files_n"] = files_n

    OUT.parent.mkdir(parents=True, exist_ok=True)

    out_text = json.dumps(payload, indent=2, sort_keys=True) + "\\n"
    if OUT.exists():
        cur = OUT.read_text(encoding="utf-8")
        if cur == out_text:
            print("OK: fingerprint already canonical (noop)")
            return

    OUT.write_text(out_text, encoding="utf-8")
    print(f"OK: wrote {OUT} (files={files_n})")


if __name__ == "__main__":
    main()
"""

    TARGET.write_text(canonical, encoding="utf-8")
    print("OK: rewrote generator canonically (schema keys preserved from existing artifact)")


if __name__ == "__main__":
    main()
