from __future__ import annotations

from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "check_python_shim_compliance_v2.sh"

BEGIN = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_BEGIN"
END = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_END"

CANON_BLOCK = """# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_BEGIN
# Bootstrap exceptions (narrow; explicit)
# - These wrappers may need to run when scripts/py is missing/empty.
# - They are permitted to use python3/python ONLY as a bootstrap fallback.
SV_PY_SHIM_COMPLIANCE_EXCEPTIONS=(
  "scripts/patch_restore_scripts_py_shim_v1.sh"
)
# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_END
"""

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"ERROR: missing {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  # 1) Ensure bounded exceptions block exists and is canonical.
  if BEGIN in txt and END in txt:
    pre, rest = txt.split(BEGIN, 1)
    mid, post = rest.split(END, 1)
    # Keep surrounding newlines stable; replace full block region.
    txt2 = pre.rstrip("\n") + "\n" + CANON_BLOCK + post.lstrip("\n")
  else:
    # Append canonical block at EOF with a leading newline.
    txt2 = txt.rstrip("\n") + "\n\n" + CANON_BLOCK

  # 2) Ensure skip logic exists: define helper + skip inside loop.
  if "is_exception_wrapper()" not in txt2:
    helper = r"""
is_exception_wrapper() {
  # $1 = wrapper path (e.g., scripts/patch_foo.sh)
  local w="$1"
  local ex
  for ex in "${SV_PY_SHIM_COMPLIANCE_EXCEPTIONS[@]:-}"; do
    if [[ "${w}" == "${ex}" ]]; then
      return 0
    fi
  done
  return 1
}
""".lstrip("\n")

    # Insert helper after has_py_shim_launcher() (right after its closing brace).
    m = re.search(r"has_py_shim_launcher\(\)\s*\{\n(?:.*\n)*?\}\n", txt2)
    if not m:
      raise SystemExit("ERROR: could not find has_py_shim_launcher() block; refusing to patch.")
    insert_at = m.end()
    txt2 = txt2[:insert_at] + "\n" + helper + "\n" + txt2[insert_at:]

  # 3) Ensure loop skips exceptions.
  # Add just after: for f in ${wrappers}; do
  loop_needle = "for f in ${wrappers}; do\n"
  if loop_needle not in txt2:
    raise SystemExit("ERROR: could not find wrappers loop; refusing to patch.")
  skip_snip = """for f in ${wrappers}; do
  if is_exception_wrapper "${f}"; then
    continue
  fi
"""
  if skip_snip not in txt2:
    txt2 = txt2.replace(loop_needle, skip_snip, 1)

  if txt2 == txt:
    print("OK: python shim compliance exceptions already canonical (noop)")
    return

  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: patched python shim compliance exceptions + skip logic (v1)")

if __name__ == "__main__":
  main()
