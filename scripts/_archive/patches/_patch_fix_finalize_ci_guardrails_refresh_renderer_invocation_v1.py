#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "scripts" / "_patch_finalize_ci_guardrails_label_registry_and_refresh_block_v1.py"

OLD = '''from pathlib import Path
import re
import sys
'''

NEW = '''from pathlib import Path
import re
import subprocess
import sys
'''

OLD_RENDER = '''def render_block() -> str:
    ns: dict[str, object] = {}
    code = RENDERER.read_text(encoding="utf-8")
    exec(compile(code, str(RENDERER), "exec"), ns)
    render_fn = ns.get("render_block_from_prove_path")
    default_prove = ns.get("DEFAULT_PROVE")
    if not callable(render_fn) or not isinstance(default_prove, Path):
        raise RuntimeError("renderer interface unexpected")
    return render_fn(default_prove)
'''

NEW_RENDER = '''def render_block() -> str:
    try:
        return subprocess.check_output(
            [sys.executable, str(RENDERER)],
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "renderer invocation failed:\\n"
            f"{exc.output}"
        ) from exc
'''

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"expected to find {label}")
    return text.replace(old, new, 1)

def main() -> int:
    if not TARGET.is_file():
        raise RuntimeError(f"missing target patcher: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    original = text

    if "import subprocess" not in text:
        text = replace_once(text, OLD, NEW, "imports")

    if "exec(compile(code, str(RENDERER), \"exec\"), ns)" in text:
        text = replace_once(text, OLD_RENDER, NEW_RENDER, "render_block implementation")
    elif "subprocess.check_output(" not in text:
        raise RuntimeError("unexpected finalize patcher state")

    if text != original:
        TARGET.write_text(text, encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
