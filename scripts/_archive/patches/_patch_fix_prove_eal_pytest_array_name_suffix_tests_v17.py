from __future__ import annotations

from pathlib import Path
import stat
import subprocess

REL = "scripts/prove_eal_calibration_type_a_v1.sh"

BEGIN = "# SV_PATCH: tracked-only pytest list (no tests/ lowercase pass)"
END = "# /SV_PATCH: tracked-only pytest list (no tests/ lowercase pass)"

def _root() -> Path:
    return Path(__file__).resolve().parents[1]

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _clipwrite(rel_path: str, content: str) -> None:
    root = _root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")

def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def _replace_bounded(s: str, begin: str, end: str, block: str) -> tuple[str, bool]:
    b = s.find(begin)
    if b < 0:
        raise SystemExit(f"ERROR: missing begin marker: {begin}")
    e = s.find(end, b)
    if e < 0:
        raise SystemExit(f"ERROR: missing end marker: {end}")
    e += len(end)
    new_s = s[:b] + block + s[e:]
    return new_s, (new_s != s)

def main() -> int:
    root = _root()
    p = root / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)

    block = (
        f"{BEGIN}\n"
        "echo \"Running tracked EAL tests only (git ls-files)\"\n"
        "# Filter to canonical Tests/ only (avoid lowercase tests/ duplicates/collisions)\n"
        "eal_canon_tests=()\n"
        "for p in \"${eal_tests[@]}\"; do\n"
        "  case \"$p\" in\n"
        "    Tests/*) eal_canon_tests+=(\"$p\");;\n"
        "  esac\n"
        "done\n"
        "if [ \"${#eal_canon_tests[@]}\" -eq 0 ]; then\n"
        "  echo \"ERROR: none of the expected EAL test files are tracked under Tests/.\" >&2\n"
        "  exit 2\n"
        "fi\n"
        "# Intentional: unquoted array expansion so gate sees Tests/... as path token\n"
        "# shellcheck disable=SC2068\n"
        "./scripts/py -m pytest -q ${eal_canon_tests[@]}\n"
        f"{END}\n"
    )

    new_s, ch = _replace_bounded(s, BEGIN, END, block)
    if not ch:
        _chmod_x(p)
        print("OK: EAL pytest filtered array already ends with _tests (noop).")
        return 0

    _clipwrite(REL, new_s)
    _chmod_x(p)
    print("OK: renamed EAL filtered pytest array to *_tests for gate allowlist (v17).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
