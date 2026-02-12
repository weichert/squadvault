from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Choose stable creative surface roots.
# Keep conservative: artifacts/exports + artifacts/creative (if present).
ROOTS = [
    REPO_ROOT / "artifacts" / "exports",
    REPO_ROOT / "artifacts" / "creative",
]

OUT = REPO_ROOT / "artifacts" / "CREATIVE_SURFACE_FINGERPRINT_v1.json"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def file_digest(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def main() -> None:
    entries = []
    for root in ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            entries.append(
                {
                    "path": rel,
                    "sha256": file_digest(p),
                    "bytes": p.stat().st_size,
                }
            )

    payload = {
        "version": 1,
        "roots": [r.relative_to(REPO_ROOT).as_posix() for r in ROOTS if r.exists()],
        "file_count": len(entries),
        "files": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: wrote {OUT} (files={len(entries)})")

if __name__ == "__main__":
    main()
