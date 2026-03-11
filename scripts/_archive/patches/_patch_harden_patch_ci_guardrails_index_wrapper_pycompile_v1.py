from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.sh")

WANT_BLOCK = """python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py

"$python" scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py
"""

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"missing target: {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  if 'py_compile scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py' in txt:
    print("OK: wrapper already includes py_compile")
    return

  anchor = 'python="${PYTHON:-python}"\n"$python" scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py'
  if anchor not in txt:
    raise SystemExit("Refusing to patch: expected python invocation anchor not found.")

  txt2 = txt.replace(
    'python="${PYTHON:-python}"\n"$python" scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py',
    WANT_BLOCK.rstrip("\n"),
    1,
  )

  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: hardened wrapper to py_compile patcher before running it")

if __name__ == "__main__":
  main()
