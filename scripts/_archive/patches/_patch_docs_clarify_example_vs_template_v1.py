from __future__ import annotations

from pathlib import Path

DOC_PATTERN = Path("docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md")
DOC_GATE = Path("docs/80_indices/ops/CI_Patcher_Wrapper_Pairing_Gate_v1.0.md")

BEGIN = "<!-- EXAMPLE_VS_TEMPLATE_CLARITY_v1_BEGIN -->"
END = "<!-- EXAMPLE_VS_TEMPLATE_CLARITY_v1_END -->"

BLOCK_PATTERN = f"""{BEGIN}
## Reference Implementation and Starting Point

**Start by copying the canonical example pair**:

- `scripts/_patch_example_noop_v1.py`
- `scripts/patch_example_noop_v1.sh`

This pair is the repository’s “golden” reference implementation for the patcher/wrapper workflow.

### About the TEMPLATE files

- `scripts/_patch_TEMPLATE_v0.py` and `scripts/patch_TEMPLATE_v0.sh` are **scaffolding only**.
- Use them only as a convenience to create a new versioned pair, then rename/version appropriately.
- Do not treat TEMPLATE files as “canonical examples” of a real repo mutation.

{END}
"""

BLOCK_GATE = f"""{BEGIN}
## Reference implementation

For the canonical patcher/wrapper workflow and the reference implementation, see:

- `docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md`
- `scripts/_patch_example_noop_v1.py` + `scripts/patch_example_noop_v1.sh`

{END}
"""

def _append_block(path: Path, block: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {path}")

    text = path.read_text()

    if BEGIN in text or END in text:
        if BEGIN in text and END in text:
            existing = text.split(BEGIN, 1)[1].split(END, 1)[0].strip()
            desired = block.split(BEGIN, 1)[1].split(END, 1)[0].strip()
            if existing == desired:
                return
            raise RuntimeError(f"{path} already contains markers but content differs; refusing to overwrite")
        raise RuntimeError(f"{path} has a partial marker; refusing to proceed")

    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block + "\n"
    path.write_text(text)

def main() -> None:
    _append_block(DOC_PATTERN, BLOCK_PATTERN)
    _append_block(DOC_GATE, BLOCK_GATE)

if __name__ == "__main__":
    main()
