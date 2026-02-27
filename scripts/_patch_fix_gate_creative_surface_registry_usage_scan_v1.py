from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "gate_creative_surface_registry_usage_v1.sh"

OLD_START = "usage_raw=\"$(\n"
OLD_END = ")\"\n"

NEW_BLOCK = """usage_raw="$(
  git grep -h -I -n -E 'CREATIVE_SURFACE_[A-Z0-9_]+' -- \\
    . \\
    ':(exclude)docs/80_indices/ops/Creative_Surface_Registry_v1.0.md' \\
    ':(exclude)**/artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json' \\
  | sed -E '/^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)(_|$)/d' \\
  | grep -Eo 'CREATIVE_SURFACE_[A-Z0-9_]+' \\
  | sed -E '/^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)(_|$)/d' \\
  | sort -u || true
)"
"""

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"ERROR: missing {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  if NEW_BLOCK in txt:
    print("OK: gate_creative_surface_registry_usage_v1 usage scan already canonical (noop)")
    return

  # Locate the existing usage_raw block by finding the first 'usage_raw="$(' and the following ')"'.
  key = 'usage_raw="$('
  i = txt.find(key)
  if i == -1:
    raise SystemExit("ERROR: could not find usage_raw block start; refusing to patch.")
  j = txt.find(')"\n', i)
  if j == -1:
    raise SystemExit("ERROR: could not find usage_raw block end; refusing to patch.")
  j += len(')"\n')

  txt2 = txt[:i] + NEW_BLOCK + txt[j:]
  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: patched gate_creative_surface_registry_usage_v1 usage scan (v1)")

if __name__ == "__main__":
  main()
