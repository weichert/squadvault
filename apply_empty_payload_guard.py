#!/usr/bin/env python3
"""Apply: silence over fabrication — skip events with empty payloads.

Problem: Events with empty payloads (e.g., test stubs) produce bullets
like "? added <?> (free agent)." because resolvers return "?"/"<?>" for
None inputs. Per governance, silence is preferred over fabrication.

Fix:
1. deterministic_bullets_v1.py — add `if not p: continue` guard
2. render_recap_text_from_facts_v1.py — add equivalent guard
3. test_deterministic_bullets_v1.py — update empty-payload test to expect silence
4. New test: verify empty-payload events produce no bullets
5. Clean test event from fixture DB
"""

import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────
# 1. Add empty-payload guard to deterministic_bullets_v1.py
# ─────────────────────────────────────────────────────────────────────

bullets_path = ROOT / "src" / "squadvault" / "core" / "recaps" / "render" / "deterministic_bullets_v1.py"
bullets_text = bullets_path.read_text()

old_block = """\
        if et in _SKIP_EVENT_TYPES:
            continue

        if et in ("TRANSACTION_TRADE", "TRADE"):"""

new_block = """\
        if et in _SKIP_EVENT_TYPES:
            continue

        # Silence over fabrication: skip events with empty payloads.
        # An empty payload means we cannot identify participants — producing
        # a bullet would yield "? added <?>" which erodes trust.
        if not p:
            continue

        if et in ("TRANSACTION_TRADE", "TRADE"):"""

assert old_block in bullets_text, "Could not find expected block in deterministic_bullets_v1.py"
bullets_text = bullets_text.replace(old_block, new_block)
bullets_path.write_text(bullets_text)
print(f"✓ Patched {bullets_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 2. Add empty-payload guard to render_recap_text_from_facts_v1.py
# ─────────────────────────────────────────────────────────────────────

facts_path = ROOT / "src" / "squadvault" / "core" / "recaps" / "render" / "render_recap_text_from_facts_v1.py"
facts_text = facts_path.read_text()

old_facts = """\
        team_name = lookup.franchise(franchise_id)

        # Prefer normalized ids (deterministic) for add/drop"""

new_facts = """\
        team_name = lookup.franchise(franchise_id)

        # Silence over fabrication: skip events with no resolvable identity.
        if not franchise_id and not norm:
            continue

        # Prefer normalized ids (deterministic) for add/drop"""

assert old_facts in facts_text, "Could not find expected block in render_recap_text_from_facts_v1.py"
facts_text = facts_text.replace(old_facts, new_facts)
facts_path.write_text(facts_text)
print(f"✓ Patched {facts_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 3. Update existing test + add new empty-payload silence test
# ─────────────────────────────────────────────────────────────────────

test_path = ROOT / "Tests" / "test_deterministic_bullets_v1.py"
test_text = test_path.read_text()

# Update existing TestNonePayload to expect silence
old_test = """\
class TestNonePayload:
    def test_none_payload_matchup(self):
        row = _row(event_type="MATCHUP_RESULT", payload=None)
        bullets = render_deterministic_bullets_v1([row])
        assert bullets == ["Unknown team beat Unknown team."]"""

new_test = (
    'class TestNonePayload:\n'
    '    def test_none_payload_produces_silence(self):\n'
    '        # None payload becomes empty dict, which produces silence.\n'
    '        row = _row(event_type="MATCHUP_RESULT", payload=None)\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert bullets == [], "Empty payload should produce silence, not a fabricated bullet"\n'
    '\n'
    '    def test_empty_dict_payload_produces_silence(self):\n'
    '        # Explicit empty dict payload produces silence.\n'
    '        row = _row(event_type="TRANSACTION_FREE_AGENT", payload={})\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert bullets == [], "Empty payload should produce silence, not \'? added <?>\'"\n'
    '\n'
    '    def test_empty_payload_skipped_among_valid_events(self):\n'
    '        # Empty payload events are skipped; valid events still render.\n'
    '        rows = [\n'
    '            _row(canonical_id="empty", event_type="TRANSACTION_FREE_AGENT", payload={}),\n'
    '            _row(canonical_id="valid", event_type="TRANSACTION_FREE_AGENT", payload={\n'
    '                "franchise_id": "F01", "player_id": "P100",\n'
    '            }),\n'
    '        ]\n'
    '        bullets = render_deterministic_bullets_v1(rows)\n'
    '        assert len(bullets) == 1\n'
    '        assert "F01 added P100 (free agent)." == bullets[0]'
)

assert old_test in test_text, "Could not find TestNonePayload in test file"
test_text = test_text.replace(old_test, new_test)

# Also update trade empty-payload test to expect silence
old_trade_test = (
    '    def test_trade_missing_fields_uses_fallbacks(self):\n'
    '        row = _row(event_type="TRADE", payload={})\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert "Unknown team acquired Unknown player from Unknown team." == bullets[0]'
)
new_trade_test = (
    '    def test_trade_missing_fields_produces_silence(self):\n'
    '        # Empty payload means no participants identifiable — silence preferred.\n'
    '        row = _row(event_type="TRADE", payload={})\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert bullets == [], "Empty payload should produce silence"'
)
assert old_trade_test in test_text, "Could not find trade missing fields test"
test_text = test_text.replace(old_trade_test, new_trade_test)

# Update unknown event type test to expect silence for empty payload
old_unknown_test = (
    '    def test_unknown_non_transaction_type_gets_generic_bullet(self):\n'
    '        row = _row(event_type="LEAGUE_EXPANSION", payload={})\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert bullets == ["League Expansion recorded."]'
)
new_unknown_test = (
    '    def test_unknown_non_transaction_type_empty_payload_silent(self):\n'
    '        # Empty payload — silence preferred even for unknown event types.\n'
    '        row = _row(event_type="LEAGUE_EXPANSION", payload={})\n'
    '        assert render_deterministic_bullets_v1([row]) == []\n'
    '\n'
    '    def test_unknown_non_transaction_type_with_payload_gets_generic_bullet(self):\n'
    '        # Non-empty payload — generic bullet still produced.\n'
    '        row = _row(event_type="LEAGUE_EXPANSION", payload={"detail": "added team"})\n'
    '        bullets = render_deterministic_bullets_v1([row])\n'
    '        assert bullets == ["League Expansion recorded."]'
)
assert old_unknown_test in test_text, "Could not find unknown event type test"
test_text = test_text.replace(old_unknown_test, new_unknown_test)

test_path.write_text(test_text)
print(f"✓ Patched {test_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 4. Clean test event from fixture DB
# ─────────────────────────────────────────────────────────────────────

fixture_db = ROOT / "fixtures" / "ci_squadvault.sqlite"
con = sqlite3.connect(str(fixture_db))

# Find and remove the test event
me_row = con.execute(
    "SELECT id FROM memory_events WHERE external_source='TEST' AND external_id='late_free_agent_1'"
).fetchone()

if me_row:
    me_id = me_row[0]
    # Remove canonical event pointing to this memory event
    con.execute("DELETE FROM canonical_events WHERE best_memory_event_id=?", (me_id,))
    # Remove the memory event
    con.execute("DELETE FROM memory_events WHERE id=?", (me_id,))
    con.commit()
    print(f"✓ Cleaned test event (memory_event id={me_id}) from fixture DB")
else:
    print("  (test event not found in fixture DB — already clean)")

con.close()


print()
print("Apply complete. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
print()
print("Then clean the test event from your local DB:")
print("  ./scripts/py -c \"")
print("import sqlite3")
print("con = sqlite3.connect('.local_squadvault.sqlite')")
print("row = con.execute(\\\"SELECT id FROM memory_events WHERE external_source='TEST' AND external_id='late_free_agent_1'\\\").fetchone()")
print("if row:")
print("    con.execute('DELETE FROM canonical_events WHERE best_memory_event_id=?', (row[0],))")
print("    con.execute('DELETE FROM memory_events WHERE id=?', (row[0],))")
print("    con.commit()")
print("    print(f'Cleaned test event id={row[0]}')")
print("else:")
print("    print('Already clean')")
print("con.close()\"")
