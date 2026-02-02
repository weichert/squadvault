from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_sanitize_pythonpath_src_python_literals_in_patchers_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # Replace the literal grep pattern with a runtime-built pattern.
    old = "xargs grep -n 'PYTHONPATH=src python' \\"
    if old not in txt:
        raise SystemExit("ERROR: could not locate expected grep line (refusing to guess)")

    new = "pat='PYTHONPATH=src '\"'\"'python'\"'\"'' \\\n  xargs grep -n \"$pat\" \\"

    out = txt.replace(old, new)
    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: patched {TARGET}")

if __name__ == '__main__':
    main()
