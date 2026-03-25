#!/usr/bin/env python3
"""
Creative layer output improvements — three fixes:

1. CLEAN EXPORT FORMAT: Add `--- SHAREABLE RECAP ---` delimiter and a
   `read` command to recap.sh that outputs only the shareable portion
   (narrative prose + facts bullets, no telemetry header).

2. HISTORICAL CALLBACKS: Strengthen the system prompt to explicitly demand
   cross-season references when the NARRATIVE ANGLES and LEAGUE HISTORY
   sections provide them. The data is already feeding correctly; the model
   just needs stronger instruction to use it.

3. NFL COLOR GUARDRAILS: Remove web_search tool from the API call. The
   NFL commentary it produces is unverified and sometimes wrong for the
   specific timing (e.g., claiming a player pickup is "savvy" when the
   player had a season-ending injury). Per governance: silence over
   fabrication. Web search can be re-added later with proper attribution.

Usage:
    python apply_creative_output_v1.py
    PYTHONPATH=src python -m pytest Tests/ -q
    git add -A && git commit -m "Creative layer output: clean format, historical callbacks, remove web search"
"""

import os
import sys


def patch_file(path, old, new, label=""):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    count = content.count(old)
    if count == 0:
        print(f"  ERROR: patch target not found in {path}: {label or old[:60]!r}")
        sys.exit(1)
    if count > 1:
        print(f"  ERROR: patch target found {count} times in {path}: {label or old[:60]!r}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  patched {path} ({label})" if label else f"  patched {path}")


def write_file(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {path}")


def main():
    # ══════════════════════════════════════════════════════════════════
    # FIX 1: Clean export format
    # ══════════════════════════════════════════════════════════════════
    print("\n=== Fix 1: Clean export format ===")

    # 1a. Change the narrative delimiter to be parseable
    patch_file(
        "src/squadvault/recaps/weekly_recap_lifecycle.py",
        old=(
            '    if _narrative_draft:\n'
            '        rendered_text = (\n'
            '            rendered_text.rstrip()\n'
            '            + "\\n\\n--- Narrative Draft (AI-assisted, requires human approval) ---\\n"\n'
            '            + _narrative_draft\n'
            '            + "\\n"\n'
            '        )'
        ),
        new=(
            '    if _narrative_draft:\n'
            '        rendered_text = (\n'
            '            rendered_text.rstrip()\n'
            '            + "\\n\\n--- SHAREABLE RECAP ---\\n"\n'
            '            + _narrative_draft\n'
            '            + "\\n--- END SHAREABLE RECAP ---\\n"\n'
            '        )'
        ),
        label="fix1-narrative-delimiter",
    )

    # 1b. Add a `read` command to recap.py that extracts just the shareable portion
    patch_file(
        "scripts/recap.py",
        old="\ndef cmd_migrate(",
        new='''\

def cmd_read(args: argparse.Namespace) -> int:
    """Read the latest recap for a week — shareable format (narrative only)."""
    _warn_if_migrations_pending(args.db)
    from squadvault.core.storage.session import DatabaseSession
    with DatabaseSession(args.db) as con:
        row = con.execute(
            """SELECT rendered_text, version, state FROM recap_artifacts
               WHERE league_id=? AND season=? AND week_index=?
                 AND artifact_type='WEEKLY_RECAP'
               ORDER BY version DESC LIMIT 1""",
            (args.league_id, args.season, args.week_index),
        ).fetchone()
    if not row or not row[0]:
        print("No recap found for that week.", file=sys.stderr)
        return 1
    rendered_text, version, state = row[0], row[1], row[2]

    # Extract shareable portion if delimiters exist
    SHARE_START = "--- SHAREABLE RECAP ---"
    SHARE_END = "--- END SHAREABLE RECAP ---"

    if SHARE_START in rendered_text:
        start = rendered_text.index(SHARE_START) + len(SHARE_START)
        end = rendered_text.index(SHARE_END) if SHARE_END in rendered_text else len(rendered_text)
        narrative = rendered_text[start:end].strip()
    else:
        # Legacy format: try old delimiter
        OLD_DELIM = "--- Narrative Draft (AI-assisted, requires human approval) ---"
        if OLD_DELIM in rendered_text:
            start = rendered_text.index(OLD_DELIM) + len(OLD_DELIM)
            narrative = rendered_text[start:].strip()
        else:
            narrative = rendered_text

    # Also extract the "What happened this week:" bullets if present
    bullets_section = ""
    BULLETS_MARKER = "What happened this week:"
    if BULLETS_MARKER in rendered_text and SHARE_START in rendered_text:
        b_start = rendered_text.index(BULLETS_MARKER)
        b_end = rendered_text.index(SHARE_START)
        bullets_section = rendered_text[b_start:b_end].strip()

    if args.format == "full":
        # Full rendered_text (including telemetry — for commissioner audit)
        print(rendered_text)
    else:
        # Shareable format
        header = f"PFL Buddies — Season {args.season}, Week {args.week_index}"
        print(header)
        print("=" * len(header))
        print()
        print(narrative)
        if bullets_section:
            print()
            print("---")
            print()
            print(bullets_section)
        print()
        state_label = f"[v{version} — {state}]"
        print(state_label)

    return 0


def cmd_migrate(''',
        label="fix1-cmd-read",
    )

    # 1c. Register the `read` subparser
    patch_file(
        "scripts/recap.py",
        old='    # migrate\n    sp = sub.add_parser(\n        "migrate",',
        new=(
            '    # read\n'
            '    sp = sub.add_parser("read", help="Read the latest recap in shareable format")\n'
            '    add_common(sp)\n'
            '    sp.add_argument("--format", choices=["share", "full"], default="share",\n'
            '                    help="share (narrative only, default) or full (with telemetry)")\n'
            '    sp.set_defaults(fn=cmd_read)\n'
            '\n'
            '    # migrate\n'
            '    sp = sub.add_parser(\n'
            '        "migrate",'
        ),
        label="fix1-read-subparser",
    )

    # ══════════════════════════════════════════════════════════════════
    # FIX 2: Strengthen historical callbacks in prompt
    # ══════════════════════════════════════════════════════════════════
    print("\n=== Fix 2: Strengthen historical callbacks ===")

    # 2a. Rewrite system prompt with stronger history instruction
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old=(
            '- Callbacks: reference earlier weeks when the data supports it ("remember when..."). \\\n'
            '  Only callback to things in the provided context — never invent history.'
        ),
        new=(
            '- Callbacks are REQUIRED when the data supports them. The NARRATIVE ANGLES and \\\n'
            '  LEAGUE HISTORY sections contain detected cross-season hooks — USE THEM. If a \\\n'
            '  team just set an all-time scoring record, SAY SO. If two rivals have met 12 \\\n'
            '  times before, REFERENCE the series record. If a streak approaches a league \\\n'
            '  record, CALL IT OUT. These callbacks are what make the recap feel like it \\\n'
            '  comes from someone who has watched this league for years, not just this week. \\\n'
            '  Only callback to things in the provided context — never invent history.'
        ),
        label="fix2-callbacks-required",
    )

    # 2b. Add explicit instruction about NARRATIVE ANGLES in the user prompt builder
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old=(
            '    if narrative_angles:\n'
            '        parts.append("=== NARRATIVE ANGLES (detected story hooks for this week) ===")\n'
            '        parts.append(narrative_angles.strip())\n'
            '        parts.append("")'
        ),
        new=(
            '    if narrative_angles:\n'
            '        parts.append("=== NARRATIVE ANGLES (detected story hooks — USE THESE) ===")\n'
            '        parts.append("IMPORTANT: The angles below are pre-computed from 16 seasons of data.")\n'
            '        parts.append("Work the HEADLINE and NOTABLE angles into your prose naturally.")\n'
            '        parts.append("These are the hooks that make the recap feel historically informed.")\n'
            '        parts.append(narrative_angles.strip())\n'
            '        parts.append("")'
        ),
        label="fix2-angles-instruction",
    )

    # 2c. Strengthen the league history section header
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old='        parts.append("=== LEAGUE HISTORY (all-time records, cross-season) ===")',
        new=(
            '        parts.append("=== LEAGUE HISTORY (all-time records, cross-season — REFERENCE THIS) ===")\n'
            '        parts.append("Use this data for context: all-time records, scoring records, streaks.")\n'
            '        parts.append("When a score approaches a league record or a team\'s record is notable, mention it.")'
        ),
        label="fix2-history-header",
    )

    # ══════════════════════════════════════════════════════════════════
    # FIX 3: Remove web_search tool from API call
    # ══════════════════════════════════════════════════════════════════
    print("\n=== Fix 3: Remove web search from creative layer ===")

    # 3a. Remove the web_search tool from the API call
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old=(
            '        message = client.messages.create(\n'
            '            model=_MODEL,\n'
            '            max_tokens=_MAX_TOKENS,\n'
            '            temperature=temperature,\n'
            '            system=system_prompt,\n'
            '            messages=[{"role": "user", "content": user_prompt}],\n'
            '            tools=[{"type": "web_search_20250305", "name": "web_search"}],\n'
            '        )'
        ),
        new=(
            '        # SV_NO_WEB_SEARCH: Web search removed to prevent unverified NFL\n'
            '        # commentary from being injected into league recaps. The creative\n'
            '        # layer must work only with league-sourced data. Per governance:\n'
            '        # silence over fabrication. Web search may be re-added later with\n'
            '        # proper attribution and verification guardrails.\n'
            '        message = client.messages.create(\n'
            '            model=_MODEL,\n'
            '            max_tokens=_MAX_TOKENS,\n'
            '            temperature=temperature,\n'
            '            system=system_prompt,\n'
            '            messages=[{"role": "user", "content": user_prompt}],\n'
            '        )'
        ),
        label="fix3-remove-web-search",
    )

    # 3b. Remove the NFL awareness rule from the system prompt since
    #     web search is no longer available
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old=(
            '- NFL awareness: if web search results give you injury/bye/breakout context for a \\\n'
            '  transaction, weave it in naturally. But NFL news is color — not league fact.'
        ),
        new=(
            '- NFL awareness: you may use general football knowledge (positions, team names, \\\n'
            '  typical fantasy value) but NEVER claim specific NFL news events (injuries, \\\n'
            '  suspensions, roster moves) unless that information is explicitly in the \\\n'
            '  provided context. When in doubt, describe what happened in the league without \\\n'
            '  speculating about why.'
        ),
        label="fix3-nfl-awareness-rule",
    )

    # 3c. Remove the NFL color hard rule since it referenced web search
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old='- NFL context from web search is background color only. It never becomes a league fact.\n',
        new='- NEVER inject NFL news, injury reports, or real-world football events not present in the data.\n',
        label="fix3-nfl-hard-rule",
    )

    # 3d. Remove the _extract_text_from_response tool_use handling since
    #     we no longer use tools — simplify to direct text extraction
    patch_file(
        "src/squadvault/ai/creative_layer_v1.py",
        old=(
            'def _extract_text_from_response(message) -> str:\n'
            '    """Extract text content from an API response, handling tool_use blocks.\n'
            '\n'
            '    When web search is enabled, the response may contain tool_use and\n'
            '    tool_result blocks interleaved with text. We extract only text blocks.\n'
            '    """\n'
            '    if not message.content:\n'
            '        return ""\n'
            '    texts = []\n'
            '    for block in message.content:\n'
            '        if hasattr(block, "text") and block.text:\n'
            '            texts.append(block.text.strip())\n'
            '    return "\\n\\n".join(texts)'
        ),
        new=(
            'def _extract_text_from_response(message) -> str:\n'
            '    """Extract text content from an API response.\n'
            '\n'
            '    Returns the first text block from the response content.\n'
            '    """\n'
            '    if not message.content:\n'
            '        return ""\n'
            '    texts = []\n'
            '    for block in message.content:\n'
            '        if hasattr(block, "text") and block.text:\n'
            '            texts.append(block.text.strip())\n'
            '    return "\\n\\n".join(texts)'
        ),
        label="fix3-simplify-extract",
    )

    # ══════════════════════════════════════════════════════════════════
    # TESTS
    # ══════════════════════════════════════════════════════════════════
    print("\n=== Adding tests ===")

    write_file("Tests/test_creative_output_v1.py", '''\
"""Tests for creative layer output improvements.

Fix 1: SHAREABLE RECAP delimiter is present and parseable
Fix 2: Narrative angles instruction is in the prompt
Fix 3: Web search tool is NOT in the API call
"""
from __future__ import annotations

import inspect
import os

import pytest


class TestShareableDelimiter:
    """The rendered_text should use parseable SHAREABLE RECAP delimiters."""

    def test_delimiter_constant_in_lifecycle(self):
        """The lifecycle must use the --- SHAREABLE RECAP --- delimiter."""
        import squadvault.recaps.weekly_recap_lifecycle as lc
        source = inspect.getsource(lc)
        assert "--- SHAREABLE RECAP ---" in source
        assert "--- END SHAREABLE RECAP ---" in source

    def test_old_delimiter_not_used(self):
        """The old narrative draft delimiter should not be used for new artifacts."""
        import squadvault.recaps.weekly_recap_lifecycle as lc
        source = inspect.getsource(lc)
        assert "Narrative Draft (AI-assisted" not in source


class TestHistoricalCallbacks:
    """The system prompt should demand historical callbacks."""

    def test_callbacks_required_in_prompt(self):
        """System prompt must instruct callbacks as REQUIRED."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "Callbacks are REQUIRED" in _SYSTEM_PROMPT

    def test_angles_instruction_in_user_prompt(self):
        """User prompt builder must instruct the model to USE narrative angles."""
        from squadvault.ai.creative_layer_v1 import _build_user_prompt
        prompt = _build_user_prompt(
            facts_bullets=["test"],
            eal_directive="MODERATE_CONFIDENCE_ONLY",
            league_id="70985",
            season=2024,
            week_index=1,
            narrative_angles="[HEADLINE] Test angle",
        )
        assert "USE THESE" in prompt
        assert "16 seasons" in prompt


class TestNoWebSearch:
    """The creative layer must NOT use web search tools."""

    def test_no_web_search_in_api_call(self):
        """The API call source must not contain web_search tool config."""
        from squadvault.ai import creative_layer_v1 as cl
        source = inspect.getsource(cl.draft_narrative_v1)
        assert "web_search" not in source

    def test_no_nfl_web_search_in_system_prompt(self):
        """System prompt must not reference web search results."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "web search" not in _SYSTEM_PROMPT.lower()

    def test_nfl_guardrail_present(self):
        """System prompt must restrict NFL claims to provided context only."""
        from squadvault.ai.creative_layer_v1 import _SYSTEM_PROMPT
        assert "NEVER inject NFL news" in _SYSTEM_PROMPT


class TestReadSubcommand:
    """The read subcommand should be registered in recap.py."""

    def test_subcommand_exists(self):
        import importlib.util
        recap_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "recap.py"
        )
        spec = importlib.util.spec_from_file_location("recap_cli", recap_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        parser = mod.build_parser()
        args = parser.parse_args([
            "read",
            "--db", "/tmp/test.db",
            "--league-id", "70985",
            "--season", "2024",
            "--week-index", "1",
        ])
        assert args.cmd == "read"
        assert hasattr(args, "fn")
''')

    print("\n=== All patches applied. ===")
    print("\nVerification:")
    print("  PYTHONPATH=src python -m pytest Tests/ -q")
    print("\nCommit:")
    print('  git add -A && git commit -m "Creative layer output: clean format, historical callbacks, remove web search"')
    print("\nThen regenerate and read:")
    print("  ./scripts/recap.sh regen --db .local_squadvault.sqlite \\")
    print("    --league-id 70985 --season 2024 --week-index 1 \\")
    print('    --reason "output improvements" --created-by steve --force')
    print("  ./scripts/recap.sh read --db .local_squadvault.sqlite \\")
    print("    --league-id 70985 --season 2024 --week-index 1")


if __name__ == "__main__":
    main()
