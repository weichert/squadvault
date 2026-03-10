from __future__ import annotations

from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).with_name("_patch_repair_ops_label_registry_parity_state_v6.py")),
    run_name="__main__",
)
