from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

NEEDLE_IMPORT_BLOCK = "from squadvault.recaps.writing_room.selection_set_schema_v1 import ("
DETAIL_PATTERN = re.compile(r"ExcludedSignal\((?P<body>[^)]*?)\bdetail\s*=\s*(?P<expr>[^,\n)]+)", re.S)

def ensure_reason_detail_import(src: str) -> str:
    if "ReasonDetailKV" in src:
        return src
    if NEEDLE_IMPORT_BLOCK not in src:
        raise SystemExit("ERROR: expected schema import block not found; refusing to patch.")
    # insert ReasonDetailKV into the import tuple
    # Put it near ExcludedSignal for readability.
    src2 = src.replace(
        "    ExcludedSignal,\n",
        "    ExcludedSignal,\n    ReasonDetailKV,\n",
        1,
    )
    if src2 == src:
        # fallback: append before closing paren
        src2 = src.replace(")\n", "    ReasonDetailKV,\n)\n", 1)
    return src2

def ensure_details_helper(src: str) -> str:
    if "def _details_one(" in src:
        return src
    # place helper near other helpers; after ISO_Z_SUFFIX if present, else after imports
    insert = (
        "\n\n"
        "def _details_one(k: str, v: object) -> list[ReasonDetailKV]:\n"
        "    return [ReasonDetailKV(k=k, v=str(v))]\n"
    )

    if "ISO_Z_SUFFIX" in src:
        # insert right after ISO_Z_SUFFIX definition
        src2 = re.sub(r"(ISO_Z_SUFFIX\s*=\s*[^\n]+\n)", r"\\1" + insert + "\n", src, count=1)
        if src2 == src:
            raise SystemExit("ERROR: failed to insert _details_one helper after ISO_Z_SUFFIX.")
        return src2

    # fallback: after __future__ import block
    m = re.search(r"from __future__ import annotations\s*\n", src)
    if not m:
        raise SystemExit("ERROR: cannot find insertion point for helper.")
    idx = m.end()
    return src[:idx] + insert + src[idx:]

def rewrite_detail_to_details(src: str) -> tuple[str, int]:
    n = 0

    # Replace all occurrences of "detail=<expr>" inside ExcludedSignal(...) with "details=_details_one('detail', <expr>)"
    def _sub(m: re.Match) -> str:
        nonlocal n
        body = m.group("body")
        expr = m.group("expr").strip()
        n += 1
        # rebuild the matched prefix + replacement; keep the rest of call intact
        # We only replace the "detail=expr" portion; everything else stays.
        return f"ExcludedSignal({body}details=_details_one('detail', {expr})"

    src2 = DETAIL_PATTERN.sub(_sub, src)

    # Hard safety check: no remaining "detail=" in ExcludedSignal calls
    if "ExcludedSignal" in src2 and re.search(r"ExcludedSignal\([^)]*\bdetail\s*=", src2):
        raise SystemExit("ERROR: patch incomplete; found remaining ExcludedSignal(... detail=...).")

    return src2, n

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target file: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if "ExcludedSignal(" not in src:
        raise SystemExit("ERROR: intake_v1.py has no ExcludedSignal calls; refusing to patch.")

    if "detail=" not in src:
        print("OK: no detail= found; nothing to patch.")
        return 0

    src = ensure_reason_detail_import(src)
    src = ensure_details_helper(src)
    src2, n = rewrite_detail_to_details(src)

    if src2 == src:
        raise SystemExit("ERROR: no changes made, but detail= was present. Refusing to proceed.")

    TARGET.write_text(src2, encoding="utf-8")
    print(f"OK: patched {TARGET.relative_to(ROOT)}")
    print(f"Rewrites: {n} (detail= -> details=_details_one(...))")
    print("Next: pytest -q")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
