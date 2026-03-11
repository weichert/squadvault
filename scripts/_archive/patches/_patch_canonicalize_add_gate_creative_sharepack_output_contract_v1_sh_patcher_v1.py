from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_creative_sharepack_output_contract_v1.sh")
PATCHER = Path("scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py")
WRAP = Path("scripts/patch_add_gate_creative_sharepack_output_contract_v1_sh.sh")

def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def main() -> None:
    if not GATE.exists():
        raise SystemExit(f"ERROR: expected gate file missing: {GATE}")

    gate_text = GATE.read_text(encoding="utf-8")

    # Build a canonical patcher that writes exactly the current gate contents.
    patcher_text = (
        "from __future__ import annotations\n"
        "from pathlib import Path\n\n"
        "TARGET = Path(\"scripts/gate_creative_sharepack_output_contract_v1.sh\")\n\n"
        f"GATE_TEXT = {gate_text!r}\n\n"
        "def main() -> None:\n"
        "    TARGET.parent.mkdir(parents=True, exist_ok=True)\n"
        "    TARGET.write_text(GATE_TEXT, encoding=\"utf-8\", newline=\"\\n\")\n"
        "    print(\"OK\")\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    )

    wrap_text = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "cd \"$(git rev-parse --show-toplevel)\"\n\n"
        "echo \"=== Patch: add scripts/gate_creative_sharepack_output_contract_v1.sh ===\"\n\n"
        "python -m py_compile scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py\n"
        "./scripts/py scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py\n\n"
        "chmod +x scripts/gate_creative_sharepack_output_contract_v1.sh\n\n"
        "bash -n scripts/gate_creative_sharepack_output_contract_v1.sh\n"
        "bash -n scripts/patch_add_gate_creative_sharepack_output_contract_v1_sh.sh\n\n"
        "echo \"OK\"\n"
    )

    _write(PATCHER, patcher_text)
    _write(WRAP, wrap_text)
    print("OK")

if __name__ == "__main__":
    main()
