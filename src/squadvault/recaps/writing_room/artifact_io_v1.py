"""
Writing Room Artifact IO v1.0 — deterministic JSON writer

Scope:
- Serialize SelectionSetV1 to canonical JSON (sorted keys, compact separators)
- Write to disk (atomic replace)

Non-scope:
- No DB writes
- No logging framework integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from squadvault.recaps.writing_room.selection_set_schema_v1 import SelectionSetV1


def write_selection_set_v1(path: Union[str, Path], selection_set: SelectionSetV1) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(selection_set.to_canonical_json() + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


__all__ = [
    "write_selection_set_v1",
]
