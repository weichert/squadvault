"""Clean plain_text recap assembly (v1) — the distributed S1-S5 artifact form.

Narrative Presentation Spec v1.0, channel `group_text_paste_assist` (the operative
channel). This is the canonical clean form a member reads: title block + setext
underline, narrative prose, separator, transactions block. It is what the E1.5b
presentation lint judges and what the distribution path emits.

Pure: deterministic string assembly, no DB / network / clock. Previously inlined in
scripts/distribute_recap.py (_format_for_paste_assist); lifted to render/ so the
distribution path and the Office review surface share one assembler (D-F / R5).
"""
from __future__ import annotations

from squadvault.core.recaps.render.presentation_lint_v1 import (
    render_transactions_block_v1,
)


def render_plain_text_recap_v1(
    *,
    narrative: str,
    bullets: list[str],
    season: int,
    week_index: int,
) -> str:
    """Compose the clean plain_text recap body (spec S1-S5).

    S1 title + setext underline; S2/S3 narrative; S4 '---' separator and S5
    transactions block only when bullets are present (quiet weeks omit S4/S5).
    Trailing newline matches the historical paste-assist output.
    """
    header = f"PFL Buddies — Season {season}, Week {week_index}"
    parts: list[str] = [header, "=" * len(header), "", narrative]
    if bullets:
        block = render_transactions_block_v1(bullets, bullet_prefix="- ")
        parts.extend(["", "---", "", block])
    return "\n".join(parts).rstrip() + "\n"
