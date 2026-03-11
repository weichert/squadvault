from __future__ import annotations

from pathlib import Path

TARGET = Path("requirements.txt")
PIN = "pytest==8.2.2"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")
    lines = [ln.rstrip("\n") for ln in txt.splitlines()]

    # If already present (any pytest pin), no-op.
    for ln in lines:
        if ln.strip().startswith("pytest=="):
            print("OK: pytest already pinned (no-op)")
            return
        if ln.strip() == "pytest":
            raise SystemExit("ERROR: found unpinned 'pytest' (refusing; must be pinned)")

    # Append with a newline separator if needed.
    out_lines = list(lines)
    if out_lines and out_lines[-1].strip() != "":
        out_lines.append("")
    out_lines.append(PIN)
    out = "\n".join(out_lines) + "\n"

    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: appended {PIN} to {TARGET}")

if __name__ == "__main__":
    main()
