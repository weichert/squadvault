from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Canonical contract surface: docs/contracts + docs/contracts/README.md + docs/contracts/*.md
CONTRACT_DIR = REPO_ROOT / "docs" / "contracts"
OUT = REPO_ROOT / "docs" / "contracts" / "CONTRACT_SURFACE_MANIFEST_v1.json"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def main() -> None:
    if not CONTRACT_DIR.exists():
        raise SystemExit(f"ERROR: missing contracts dir: {CONTRACT_DIR}")

    files = []
    for p in sorted(CONTRACT_DIR.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        # include everything under docs/contracts (manifest should be explicit)
        files.append(
            {
                "path": rel,
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
            }
        )

    manifest = {
        "version": 1,
        "root": "docs/contracts",
        "file_count": len(files),
        "files": files,
    }

    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: wrote {OUT} (files={len(files)})")

if __name__ == "__main__":
    main()
