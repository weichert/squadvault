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
