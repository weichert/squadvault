#!/usr/bin/env python3
"""Fix TestLiveAPI.test_live_narrative_draft: skip when anthropic package not installed.

The test gates on ANTHROPIC_API_KEY but not on the package being importable.
When the key is set but the package isn't installed, the function silently
returns None and the test fails instead of skipping.
"""
import sys

def patch_file(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.count(old) != 1:
        print(f"ERROR: expected exactly 1 match in {path}")
        sys.exit(1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  patched {path}")

patch_file(
    "Tests/test_creative_layer_rivalry_v1.py",
    '    @pytest.mark.skipif(\n'
    '        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),\n'
    '        reason="ANTHROPIC_API_KEY not set — skipping live API test",\n'
    '    )\n'
    '    def test_live_narrative_draft(self):',

    '    @pytest.mark.skipif(\n'
    '        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),\n'
    '        reason="ANTHROPIC_API_KEY not set — skipping live API test",\n'
    '    )\n'
    '    @pytest.mark.skipif(\n'
    '        not __import__("importlib").util.find_spec("anthropic"),\n'
    '        reason="anthropic package not installed — skipping live API test",\n'
    '    )\n'
    '    def test_live_narrative_draft(self):',
)

print("\nDone. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
print("Expected: 1109 passed, 3 skipped")
print('\nCommit:')
print('  git add -A && git commit -m "Fix live API test: skip when anthropic package not installed"')
