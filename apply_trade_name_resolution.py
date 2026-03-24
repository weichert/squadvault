#!/usr/bin/env python3
"""Apply: Extract MFL trade player/franchise IDs for name resolution.

Problem: Trade bullets show raw player IDs ("traded 15754 to...") because
_collect_ids_from_payloads doesn't extract IDs from raw_mfl_json, so the
PlayerResolver never loads names for trade participants.

Fix: Parse raw_mfl_json in _collect_ids_from_payloads to extract franchise
and player IDs for resolver pre-loading.

Changes:
  src/squadvault/recaps/weekly_recap_lifecycle.py  (patch _collect_ids_from_payloads)
  Tests/test_name_resolution_v1.py                 (add MFL trade ID extraction test)
"""

import pathlib

ROOT = pathlib.Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────
# 1. Patch _collect_ids_from_payloads in weekly_recap_lifecycle.py
# ─────────────────────────────────────────────────────────────────────

lifecycle_path = ROOT / "src" / "squadvault" / "recaps" / "weekly_recap_lifecycle.py"
lifecycle_text = lifecycle_path.read_text()

old_block = """\
        # Handle list-valued player IDs (added/dropped)
        for key in ("players_added_ids", "players_dropped_ids"):
            v = p.get(key)
            if isinstance(v, list):
                for item in v:
                    if item is not None:
                        player_ids.add(str(item).strip())
            elif isinstance(v, str) and v.strip():
                for item in v.split(","):
                    s = item.strip()
                    if s:
                        player_ids.add(s)

    player_ids.discard("")"""

new_block = """\
        # Handle list-valued player IDs (added/dropped)
        for key in ("players_added_ids", "players_dropped_ids"):
            v = p.get(key)
            if isinstance(v, list):
                for item in v:
                    if item is not None:
                        player_ids.add(str(item).strip())
            elif isinstance(v, str) and v.strip():
                for item in v.split(","):
                    s = item.strip()
                    if s:
                        player_ids.add(s)

        # Extract IDs from embedded MFL trade JSON (franchise + player IDs)
        raw_mfl = p.get("raw_mfl_json")
        if raw_mfl and isinstance(raw_mfl, str):
            try:
                mfl = json.loads(raw_mfl)
                if isinstance(mfl, dict):
                    for fkey in ("franchise", "franchise2"):
                        fv = mfl.get(fkey)
                        if fv:
                            franchise_ids.add(str(fv).strip())
                    for pkey in ("franchise1_gave_up", "franchise2_gave_up"):
                        pv = mfl.get(pkey, "")
                        if pv:
                            for pid in str(pv).split(","):
                                s = pid.strip()
                                if s:
                                    player_ids.add(s)
            except (ValueError, TypeError):
                pass

    player_ids.discard("")"""

assert old_block in lifecycle_text, "Could not find expected block in weekly_recap_lifecycle.py"
lifecycle_text = lifecycle_text.replace(old_block, new_block)
lifecycle_path.write_text(lifecycle_text)
print(f"Patched {lifecycle_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 2. Add test for MFL trade ID extraction
# ─────────────────────────────────────────────────────────────────────

test_path = ROOT / "Tests" / "test_name_resolution_v1.py"
test_text = test_path.read_text()

# Add CanonicalEventRow import
old_import = "from squadvault.recaps.weekly_recap_lifecycle import ("
new_import = "from squadvault.core.recaps.render.deterministic_bullets_v1 import CanonicalEventRow\nfrom squadvault.recaps.weekly_recap_lifecycle import ("

assert old_import in test_text, "Could not find lifecycle import in test file"
test_text = test_text.replace(old_import, new_import, 1)

# Append MFL trade test
mfl_test = '''

    def test_collect_ids_extracts_mfl_trade_json(self, nr_db):
        # MFL trades embed franchise + player IDs in raw_mfl_json
        row = CanonicalEventRow(
            canonical_id="trade_test",
            occurred_at="2024-09-12T00:00:00Z",
            event_type="TRANSACTION_TRADE",
            payload={
                "franchise_id": "0004",
                "raw_mfl_json": '{"franchise":"0004","franchise2":"0010",'
                               '"franchise1_gave_up":"15754,","franchise2_gave_up":"16214,",'
                               '"timestamp":"1726111841","type":"TRADE"}',
            },
        )
        player_ids, franchise_ids = _collect_ids_from_payloads([row])
        assert "15754" in player_ids, "Player ID from franchise1_gave_up"
        assert "16214" in player_ids, "Player ID from franchise2_gave_up"
        assert "0004" in franchise_ids, "Franchise from raw_mfl_json"
        assert "0010" in franchise_ids, "Franchise2 from raw_mfl_json"
'''

test_text = test_text.rstrip() + "\n" + mfl_test
test_path.write_text(test_text)
print(f"Patched {test_path.relative_to(ROOT)}")


print()
print("Apply complete. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
print()
print("Then reprocess week 1 with your API key to see resolved trade names:")
print("  ANTHROPIC_API_KEY=sk-ant-... ./scripts/py scripts/reprocess_full_season.py \\")
print("      --db .local_squadvault.sqlite --league-id 70985 --season 2024 \\")
print("      --start-week 1 --end-week 1 --execute")
