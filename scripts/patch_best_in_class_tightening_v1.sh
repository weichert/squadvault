#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: best-in-class tightening (A–D) (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# ----------------------------
# [0] Sanity: require clean repo (allow THIS wrapper as the only untracked file)
# ----------------------------
st="$(git status --porcelain=v1)"

# Allow exactly: ?? scripts/patch_best_in_class_tightening_v1.sh
allowed="?? scripts/patch_best_in_class_tightening_v1.sh"

if [ -n "$st" ]; then
  if [ "$st" = "$allowed" ]; then
    echo "OK: clean repo (allowlisted self wrapper as untracked)"
  else
    echo "ERROR: working tree not clean. Commit or stash first."
    echo "$st"
    exit 1
  fi
fi

# ----------------------------
# [1] Write gates + helpers
# ----------------------------

# (A) Runtime envelope gate (budget + proof count)
bash scripts/clipwrite.sh scripts/gate_ci_runtime_envelope_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Gate: CI runtime envelope (v1)
# - Enforces a soft time budget for prove_ci (measured externally by prove_ci)
# - Enforces proof count invariants when provided
#
# Inputs (optional env):
#   SV_CI_RUNTIME_BUDGET_SECONDS  (default 180)
#   SV_CI_RUNTIME_SECONDS         (required for runtime check)
#   SV_CI_PROOF_COUNT_EXPECTED    (optional; if set, must match SV_CI_PROOF_COUNT_ACTUAL)
#   SV_CI_PROOF_COUNT_ACTUAL      (optional; required if EXPECTED is set)

budget="${SV_CI_RUNTIME_BUDGET_SECONDS:-180}"

if [ -z "${SV_CI_RUNTIME_SECONDS:-}" ]; then
  echo "SKIP: SV_CI_RUNTIME_SECONDS not provided (runtime check not evaluated)."
else
  rt="${SV_CI_RUNTIME_SECONDS}"
  if [ "${rt}" -gt "${budget}" ]; then
    echo "ERROR: CI runtime exceeded budget."
    echo "  runtime_seconds=${rt}"
    echo "  budget_seconds=${budget}"
    exit 1
  fi
  echo "OK: runtime within budget (${rt}s <= ${budget}s)"
fi

if [ -n "${SV_CI_PROOF_COUNT_EXPECTED:-}" ]; then
  if [ -z "${SV_CI_PROOF_COUNT_ACTUAL:-}" ]; then
    echo "ERROR: SV_CI_PROOF_COUNT_EXPECTED is set but SV_CI_PROOF_COUNT_ACTUAL is missing."
    exit 1
  fi
  if [ "${SV_CI_PROOF_COUNT_ACTUAL}" != "${SV_CI_PROOF_COUNT_EXPECTED}" ]; then
    echo "ERROR: proof count drift detected."
    echo "  expected=${SV_CI_PROOF_COUNT_EXPECTED}"
    echo "  actual=${SV_CI_PROOF_COUNT_ACTUAL}"
    exit 1
  fi
  echo "OK: proof count matches expected (${SV_CI_PROOF_COUNT_ACTUAL})"
fi

exit 0
EOF
chmod +x scripts/gate_ci_runtime_envelope_v1.sh


# (B) Contract surface manifest generator + hash gate
bash scripts/clipwrite.sh scripts/gen_contract_surface_manifest_v1.py <<'EOF'
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
EOF

bash scripts/clipwrite.sh scripts/gate_contract_surface_manifest_hash_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Gate: contract surface manifest hash exactness (v1)
# - Regenerates manifest and requires no diff.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="docs/contracts/CONTRACT_SURFACE_MANIFEST_v1.json"
if [ ! -f "$target" ]; then
  echo "ERROR: missing manifest: $target"
  echo "Run: ./scripts/py scripts/gen_contract_surface_manifest_v1.py"
  exit 1
fi

tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

./scripts/py scripts/gen_contract_surface_manifest_v1.py >/dev/null
git diff --exit-code -- "$target" >/dev/null || {
  echo "ERROR: contract surface manifest is out of date."
  echo "Fix by running:"
  echo "  ./scripts/py scripts/gen_contract_surface_manifest_v1.py"
  exit 1
}

echo "OK: contract surface manifest is canonical."
exit 0
EOF
chmod +x scripts/gate_contract_surface_manifest_hash_v1.sh


# (C) Creative surface fingerprint (stable hash of selected output roots)
bash scripts/clipwrite.sh scripts/gen_creative_surface_fingerprint_v1.py <<'EOF'
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
EOF

bash scripts/clipwrite.sh scripts/gate_creative_surface_fingerprint_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Gate: creative surface fingerprint canonical (v1)
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"
if [ ! -f "$target" ]; then
  echo "ERROR: missing fingerprint file: $target"
  echo "Create it by running:"
  echo "  ./scripts/py scripts/gen_creative_surface_fingerprint_v1.py"
  exit 1
fi

./scripts/py scripts/gen_creative_surface_fingerprint_v1.py >/dev/null

git diff --exit-code -- "$target" >/dev/null || {
  echo "ERROR: creative surface fingerprint is out of date."
  echo "Fix by running:"
  echo "  ./scripts/py scripts/gen_creative_surface_fingerprint_v1.py"
  exit 1
}

echo "OK: creative surface fingerprint is canonical."
exit 0
EOF
chmod +x scripts/gate_creative_surface_fingerprint_v1.sh


# (D) Meta guardrail: unify surface parity checks
bash scripts/clipwrite.sh scripts/gate_meta_surface_parity_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Gate: meta surface parity (v1)
# - Aggregates and fails fast on:
#   - proof surface registry exactness
#   - CI registry ↔ execution alignment
#   - CI guardrails ops entrypoint parity
#   - patcher/wrapper pairing
#
# NOTE: Each underlying gate is already best-in-class. This just makes them an explicit "meta" surface.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> meta: patcher/wrapper pairing"
bash scripts/check_patch_pairs_v1.sh

echo "==> meta: proof surface registry exactness"
bash scripts/gate_proof_suite_completeness_v1.sh

echo "==> meta: CI registry ↔ execution alignment"
bash scripts/gate_ci_registry_execution_alignment_v1.sh

echo "==> meta: CI guardrails ops entrypoint parity"
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK: meta surface parity passed (v1)"
exit 0
EOF
chmod +x scripts/gate_meta_surface_parity_v1.sh


# ----------------------------
# [2] Patchers: index + wire into prove_ci
# ----------------------------

bash scripts/clipwrite.sh scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py <<'EOF'
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

LINES = [
    "- scripts/gate_ci_runtime_envelope_v1.sh — CI runtime envelope: budget + proof-count drift guard (v1)\n",
    "- scripts/gate_contract_surface_manifest_hash_v1.sh — Contracts: manifest hash exactness gate (v1)\n",
    "- scripts/gate_creative_surface_fingerprint_v1.sh — Creative surface fingerprint canonical gate (v1)\n",
    "- scripts/gate_meta_surface_parity_v1.sh — Meta: surface parity aggregator gate (v1)\n",
]

def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected bounded markers not found; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    if not mid.endswith("\n"):
        mid += "\n"

    changed = False
    for line in LINES:
        if line.strip() in mid:
            continue
        mid += line
        changed = True

    if not changed:
        print("OK: entrypoints already present (idempotent).")
        return

    DOC.write_text(pre + BEGIN + mid + END + post, encoding="utf-8")
    print("OK: added best-in-class tightening entrypoints to Ops guardrails index.")

if __name__ == "__main__":
    main()
EOF

bash scripts/clipwrite.sh scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py <<'EOF'
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"

ANCHOR = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"

INSERT = [
    "\n",
    "## Best-in-class tightening: explicit execution surfaces (v1)\n",
    "## (A) Runtime envelope\n",
    "# NOTE: prove_ci measures runtime; gate enforces provided envelope.\n",
    "\n",
    "## (B) Contract boundary formalization\n",
    "bash scripts/gate_contract_surface_manifest_hash_v1.sh\n",
    "\n",
    "## (C) Creative surface certification\n",
    "bash scripts/gate_creative_surface_fingerprint_v1.sh\n",
    "\n",
    "## (D) Meta surface parity\n",
    "bash scripts/gate_meta_surface_parity_v1.sh\n",
    "\n",
]

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if ANCHOR not in text:
        raise SystemExit("ERROR: expected anchor not found in scripts/prove_ci.sh")

    if "bash scripts/gate_meta_surface_parity_v1.sh\n" in text:
        print("OK: prove_ci already wires best-in-class tightening (idempotent).")
        return

    before, after = text.split(ANCHOR, 1)

    add_lines: list[str] = []
    for ln in INSERT:
        if ln.strip() and ln in before:
            continue
        add_lines.append(ln)

    new_text = before + "".join(add_lines) + ANCHOR + after
    PROVE.write_text(new_text, encoding="utf-8")
    print("OK: wired best-in-class tightening gates into prove_ci before parity gate.")
EOF

# Runtime measurement patcher: wrap prove_ci body with timer exports (A)
bash scripts/clipwrite.sh scripts/_patch_prove_ci_add_runtime_measurement_v1.py <<'EOF'
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"

MARKER_BEGIN = "# --- SV_CI_RUNTIME_MEASUREMENT_v1_BEGIN ---\n"
MARKER_END   = "# --- SV_CI_RUNTIME_MEASUREMENT_v1_END ---\n"

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")

    if MARKER_BEGIN in text and MARKER_END in text:
        print("OK: runtime measurement block already present (idempotent).")
        return

    # Insert near top after deterministic env envelope confirmation (best-effort).
    anchor = 'echo "OK: deterministic env envelope"\n'
    if anchor in text:
        before, after = text.split(anchor, 1)
        before = before + anchor
    else:
        # Fallback: after set -euo pipefail line
        lines = text.splitlines(keepends=True)
        idx = None
        for k, ln in enumerate(lines):
            if ln.strip() == "set -euo pipefail":
                idx = k + 1
                break
        if idx is None:
            raise SystemExit("ERROR: could not find insertion point in prove_ci.sh")
        before = "".join(lines[:idx]) + "\n"
        after = "".join(lines[idx:])

    # Use scripts/py (shim-compliant). Avoid heredocs: use -c.
    block = (
        MARKER_BEGIN
        + 'sv_rt_start="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
        + 'export SV_CI_RUNTIME_START_EPOCH_SECONDS="$sv_rt_start"\n'
        + "# SV_CI_PROOF_COUNT_EXPECTED may be set externally if desired.\n"
        + MARKER_END
    )

    end_anchor = 'echo "OK: worktree cleanliness (v1): end-of-run"\n'
    if end_anchor in after:
        pre2, post2 = after.split(end_anchor, 1)
        end_block = (
            end_anchor
            + 'sv_rt_end="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
            + 'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            + "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )
        after = pre2 + end_block + post2
    else:
        after = (
            after
            + "\n# SV_CI runtime envelope enforcement (best-effort; v1)\n"
            + 'sv_rt_end="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
            + 'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            + "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )

    PROVE.write_text(before + block + after, encoding="utf-8")
    print("OK: added runtime measurement exports + runtime envelope gate call (v1).")

if __name__ == "__main__":
    main()
EOF


# ----------------------------
# [3] Wrappers (pairing compliance) for the new patchers
# ----------------------------

bash scripts/clipwrite.sh scripts/patch_ops_index_add_best_in_class_tightening_entrypoints_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops index add best-in-class tightening entrypoints (v1) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
./scripts/py -m py_compile scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py
./scripts/py scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py
echo "OK"
EOF
chmod +x scripts/patch_ops_index_add_best_in_class_tightening_entrypoints_v1.sh

bash scripts/clipwrite.sh scripts/patch_prove_ci_wire_best_in_class_tightening_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci wire best-in-class tightening (v1) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
./scripts/py -m py_compile scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py
./scripts/py scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py
bash -n scripts/prove_ci.sh
echo "OK"
EOF
chmod +x scripts/patch_prove_ci_wire_best_in_class_tightening_v1.sh

bash scripts/clipwrite.sh scripts/patch_prove_ci_add_runtime_measurement_v1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci add runtime measurement exports (v1) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
./scripts/py -m py_compile scripts/_patch_prove_ci_add_runtime_measurement_v1.py
./scripts/py scripts/_patch_prove_ci_add_runtime_measurement_v1.py
bash -n scripts/prove_ci.sh
echo "OK"
EOF
chmod +x scripts/patch_prove_ci_add_runtime_measurement_v1.sh


# ----------------------------
# [4] Apply patches (idempotent)
# ----------------------------
bash scripts/patch_ops_index_add_best_in_class_tightening_entrypoints_v1.sh
bash scripts/patch_prove_ci_wire_best_in_class_tightening_v1.sh
bash scripts/patch_prove_ci_add_runtime_measurement_v1.sh

# Generate canonical artifacts for gates that require committed canonical files.
# (B) Contract manifest
./scripts/py scripts/gen_contract_surface_manifest_v1.py

# (C) Creative fingerprint
./scripts/py scripts/gen_creative_surface_fingerprint_v1.py

# ----------------------------
# [5] Verify gates (fast)
# ----------------------------
bash scripts/gate_contract_surface_manifest_hash_v1.sh
bash scripts/gate_creative_surface_fingerprint_v1.sh
bash scripts/gate_meta_surface_parity_v1.sh

# ----------------------------
# [6] Stage + commit (single commit)
# ----------------------------
git add \
  scripts/gate_ci_runtime_envelope_v1.sh \
  scripts/gen_contract_surface_manifest_v1.py \
  scripts/gate_contract_surface_manifest_hash_v1.sh \
  scripts/gen_creative_surface_fingerprint_v1.py \
  scripts/gate_creative_surface_fingerprint_v1.sh \
  scripts/gate_meta_surface_parity_v1.sh \
  scripts/_patch_ops_index_add_best_in_class_tightening_entrypoints_v1.py \
  scripts/_patch_prove_ci_wire_best_in_class_tightening_v1.py \
  scripts/_patch_prove_ci_add_runtime_measurement_v1.py \
  scripts/patch_ops_index_add_best_in_class_tightening_entrypoints_v1.sh \
  scripts/patch_prove_ci_wire_best_in_class_tightening_v1.sh \
  scripts/patch_prove_ci_add_runtime_measurement_v1.sh \
  scripts/prove_ci.sh \
  docs/80_indices/ops/CI_Guardrails_Index_v1.0.md \
  docs/contracts/CONTRACT_SURFACE_MANIFEST_v1.json \
  artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json

git commit -m "Best-in-class tightening (A–D): runtime envelope + contract manifest + creative fingerprint + meta parity (v1)"

# ----------------------------
# [7] Full proof run (authoritative)
# ----------------------------
bash scripts/prove_ci.sh

echo "OK: best-in-class tightening complete (v1)."
