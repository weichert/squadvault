from __future__ import annotations

from pathlib import Path

DOC = Path("docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
ROE = Path("docs/process/rules_of_engagement.md")

BEGIN = "<!-- PATCHER_WRAPPER_LINKS_v1_BEGIN -->"
END = "<!-- PATCHER_WRAPPER_LINKS_v1_END -->"

BLOCK = f"""{BEGIN}
## Related Process Docs

- **Canonical Patcher / Wrapper Pattern (v1.0):** `{DOC.as_posix()}`  
  Required for operational, CI, and documentation mutations. Prefer the reference implementation:
  `scripts/_patch_example_noop_v1.py` + `scripts/patch_example_noop_v1.sh`.

{END}
"""

ROE_BLOCK = f"""{BEGIN}
## Canonical Patcher / Wrapper Pattern (Required)

All operational, CI, and documentation mutations must follow the canonical patcher/wrapper workflow.

- `{DOC.as_posix()}`

{END}
"""

def _append_block(path: Path, block: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {path}")

    text = path.read_text()

    if BEGIN in text or END in text:
        # If markers exist, require exact match (no silent overwrite).
        if BEGIN in text and END in text:
            existing = text.split(BEGIN, 1)[1].split(END, 1)[0].strip()
            desired = block.split(BEGIN, 1)[1].split(END, 1)[0].strip()
            if existing == desired:
                return
            raise RuntimeError(f"{path} already contains markers but content differs; refusing to overwrite")
        raise RuntimeError(f"{path} has a partial marker; refusing to proceed")

    # Append predictably at end.
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block + "\n"
    path.write_text(text)

def main() -> None:
    if not DOC.exists():
        raise RuntimeError(f"Missing required doc target: {DOC}")

    _append_block(CI_INDEX, BLOCK)
    _append_block(ROE, ROE_BLOCK)

if __name__ == "__main__":
    main()
