from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # Idempotence: if already repo-root resolved, noop.
    if re.search(r'^\s*registry_doc="\$\{REPO_ROOT\}/docs/80_indices/ops/Creative_Surface_Registry_v1\.0\.md"\s*$',
                 src, flags=re.MULTILINE):
        print("OK: already patched (noop)")
        return

    # Require the expected legacy line (refuse on unexpected file shapes).
    legacy_pat = r'^\s*registry_doc="docs/80_indices/ops/Creative_Surface_Registry_v1\.0\.md"\s*$'
    if not re.search(legacy_pat, src, flags=re.MULTILINE):
        raise SystemExit(
            "ERROR: expected legacy registry_doc assignment not found.\n"
            "Refusing to patch to avoid corrupting an unexpected file shape."
        )

    # Ensure we have a stable REPO_ROOT computed in the script (insert once, deterministic).
    # We place it immediately after the first 'set -euo pipefail' if present, else after shebang.
    repo_root_block = (
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
    )

    if "REPO_ROOT=" not in src:
        if "set -euo pipefail" in src:
            src = src.replace(
                "set -euo pipefail\n",
                "set -euo pipefail\n\n" + repo_root_block + "\n",
                1,
            )
        else:
            # Fallback: after shebang (first line) if present.
            lines = src.splitlines(keepends=True)
            if lines and lines[0].startswith("#!"):
                src = lines[0] + "\n" + repo_root_block + "\n" + "".join(lines[1:])
            else:
                src = repo_root_block + "\n" + src

    # Replace legacy registry_doc assignment.
    src = re.sub(
        legacy_pat,
        'registry_doc="${REPO_ROOT}/docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"',
        src,
        flags=re.MULTILINE,
    )

    TARGET.write_text(src, encoding="utf-8")
    print("OK: patched registry_doc to be REPO_ROOT-resolved (v4)")

if __name__ == "__main__":
    main()
