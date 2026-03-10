from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "check_python_shim_compliance_v2.sh"

BEGIN = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_BEGIN"
END = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_END"

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"ERROR: missing {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  if BEGIN not in txt or END not in txt:
    raise SystemExit("ERROR: exceptions block markers not found; refusing to patch.")

  pre, rest = txt.split(BEGIN, 1)
  block_mid, post = rest.split(END, 1)
  block = BEGIN + block_mid + END

  # Remove existing block from current location.
  txt_wo = pre.rstrip("\n") + "\n" + post.lstrip("\n")

  if "is_exception_wrapper()" not in txt_wo:
    raise SystemExit("ERROR: is_exception_wrapper() not found; refusing to patch.")

  # Insert block immediately before is_exception_wrapper().
  needle = "is_exception_wrapper() {"
  if block + "\n\n" + needle in txt_wo or block + "\n" + needle in txt_wo:
    print("OK: python shim compliance exceptions block already positioned canonically (noop)")
    return

  if needle not in txt_wo:
    raise SystemExit("ERROR: insertion anchor not found; refusing to patch.")

  txt2 = txt_wo.replace(needle, block + "\n\n" + needle, 1)

  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: moved python shim compliance exceptions block before wrapper scan (v1)")

if __name__ == "__main__":
  main()
