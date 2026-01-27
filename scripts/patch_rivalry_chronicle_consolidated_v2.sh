#!/usr/bin/env bash
set -euo pipefail

echo "=== Consolidated Patch: Rivalry Chronicle (generate + approve + dev_env) v2 ==="
python="${PYTHON:-python}"

# ---------- Patch 1: scripts/dev_env.sh (safe to source from anywhere; do not set -euo in sourced file) ----------
$python - <<'PY'
from __future__ import annotations
from pathlib import Path
import re, sys

p = Path("scripts/dev_env.sh")
if not p.exists():
    raise SystemExit(f"ERROR: missing {p}")

s = p.read_text(encoding="utf-8")

# If already converted, leave it.
if "Source this from anywhere inside the repo" in s:
    print("OK: dev_env.sh already source-safe; no changes.")
    raise SystemExit(0)

# Replace the top comment + remove set -euo (dangerous in sourced files).
lines = s.splitlines(True)
out = []
i = 0
while i < len(lines):
    ln = lines[i]
    if i == 0 and ln.startswith("#!/usr/bin/env bash"):
        out.append(ln)
        i += 1
        continue
    # Drop old header comment and set -euo if present near top.
    if i < 12 and ("Source this from repo root" in ln or ln.strip() == "set -euo pipefail"):
        i += 1
        continue
    out.append(ln)
    i += 1

# Insert new header after shebang if not present
if out and out[0].startswith("#!/usr/bin/env bash"):
    hdr = [
        "# Source this from anywhere inside the repo:\n",
        "#   source /path/to/repo/scripts/dev_env.sh\n",
        "\n",
    ]
    out = [out[0]] + hdr + out[1:]

p.write_text("".join(out), encoding="utf-8")
print("OK: patched scripts/dev_env.sh header for source-safety.")
PY

# ---------- Patch 2: rivalry_chronicle_generate_v1.py (ensure gen.text non-empty + pass exactly one of week_indices/week_range to generator + persist) ----------
$python - <<'PY'
from __future__ import annotations
from pathlib import Path
import re

p = Path("src/squadvault/consumers/rivalry_chronicle_generate_v1.py")
if not p.exists():
    raise SystemExit(f"ERROR: missing {p}")

s = p.read_text(encoding="utf-8")

# Idempotency: if already using persist_kwargs + rendered_text=txt, do nothing.
if "persist_kwargs = dict(" in s and "rendered_text=txt" in s and "gen = generate_rivalry_chronicle_v1(" in s:
    print("OK: generate consumer already patched (gen + persist kwargs); no changes.")
    raise SystemExit(0)

# Ensure generator import exists.
if "from squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1" not in s:
    m = re.search(r"(?m)^from squadvault\.chronicle\.input_contract_v1 import MissingWeeksPolicy\s*$", s)
    if not m:
        raise SystemExit("ERROR: could not anchor MissingWeeksPolicy import to add generator import.")
    s = s[:m.end()] + "\nfrom squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1" + s[m.end():]

# Find persist call anchor (original form).
m_call = re.search(r"(?m)^([ \t]*)res\s*=\s*persist_rivalry_chronicle_v1\(\s*$", s)
if not m_call:
    # If file evolved but still calls persist, fall back to any line containing persist_rivalry_chronicle_v1(
    m_call = re.search(r"(?m)^([ \t]*)res\s*=\s*persist_rivalry_chronicle_v1\(", s)
if not m_call:
    raise SystemExit("ERROR: could not find a persist_rivalry_chronicle_v1 call (res = persist_rivalry_chronicle_v1...).")

indent = m_call.group(1)
call_start = m_call.start()

# Remove any existing week_indices/week_range kwargs inside the call if present (we will re-add via kwargs).
s2 = re.sub(r"(?m)^[ \t]*week_indices\s*=\s*week_indices,\s*\n", "", s, count=1)
s2 = re.sub(r"(?m)^[ \t]*week_range\s*=\s*week_range,\s*\n", "", s2, count=1)

# Find the closing paren of the persist call to replace the whole block.
close_pat = re.compile(rf"(?m)^{re.escape(indent)}\)\s*$")
mc = close_pat.search(s2, m_call.end())
if not mc:
    raise SystemExit("ERROR: could not locate closing ')' for persist call.")

call_end = mc.end()

block = (
    f"{indent}# SV_PATCH_V4: chronicle consumer generates gen.text before persist\n"
    f"{indent}# SV_PATCH_V4_1: pass exactly one of week_indices/week_range to generator\n"
    f"{indent}gen_kwargs = dict(\n"
    f"{indent}    db_path=args.db,\n"
    f"{indent}    league_id=int(args.league_id),\n"
    f"{indent}    season=int(args.season),\n"
    f"{indent}    missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),\n"
    f"{indent}    created_at_utc=str(args.created_at_utc),\n"
    f"{indent})\n"
    f"{indent}if week_indices is not None:\n"
    f"{indent}    gen_kwargs['week_indices'] = week_indices\n"
    f"{indent}else:\n"
    f"{indent}    gen_kwargs['week_range'] = week_range\n"
    f"{indent}gen = generate_rivalry_chronicle_v1(**gen_kwargs)\n"
    f"{indent}txt = str(getattr(gen, 'text', None) or '')\n"
    f"{indent}if not txt.strip():\n"
    f"{indent}    raise SystemExit('ERROR: rivalry_chronicle_generate_v1 produced empty gen.text; refusing to persist.')\n"
    f"{indent}# SV_PATCH_V4_2: pass exactly one of week_indices/week_range to persist\n"
    f"{indent}persist_kwargs = dict(\n"
    f"{indent}    rendered_text=txt,\n"
    f"{indent}    db_path=args.db,\n"
    f"{indent}    league_id=args.league_id,\n"
    f"{indent}    season=args.season,\n"
    f"{indent}    missing_weeks_policy=MissingWeeksPolicy(args.missing_weeks_policy),\n"
    f"{indent}    created_at_utc=args.created_at_utc,\n"
    f"{indent})\n"
    f"{indent}if week_indices is not None:\n"
    f"{indent}    persist_kwargs['week_indices'] = week_indices\n"
    f"{indent}else:\n"
    f"{indent}    persist_kwargs['week_range'] = week_range\n"
    f"{indent}res = persist_rivalry_chronicle_v1(**persist_kwargs)\n"
)

s3 = s2[:call_start] + block + s2[call_end:]
p.write_text(s3, encoding="utf-8")
print("OK: patched generate consumer (gen.text guard + kwargs discipline).")
PY

# ---------- Patch 3: rivalry_chronicle_approve_v1.py (single unconditional guard; remove duplicates; fix ORDER BY placement; fix stray unindented LOCK comment) ----------
$python - <<'PY'
from __future__ import annotations
from pathlib import Path
import re

p = Path("src/squadvault/consumers/rivalry_chronicle_approve_v1.py")
if not p.exists():
    raise SystemExit(f"ERROR: missing {p}")

s = p.read_text(encoding="utf-8")

SENT = "SV_PATCH_APPROVE_GUARD_CANON_V1: single unconditional empty-text guard (draft row; deterministic)"
if SENT in s:
    print("OK: approve guard already canonical; no changes.")
    raise SystemExit(0)

# Normalize the stray LOCK comment indentation if it appears at column 0.
# We only fix if it is immediately followed by indented code (i.e., it's inside a function logically).
s = re.sub(r"(?m)^# LOCK_E_IDEMPOTENT_IF_APPROVED_V7\s*$", "        # LOCK_E_IDEMPOTENT_IF_APPROVED_V7", s, count=1)

# Remove any existing guard blocks we previously injected (keep the file clean).
# 1) SV_PATCH_APPROVE_GUARD_* blocks
s = re.sub(
    r"(?ms)^[ \t]*# SV_PATCH_APPROVE_GUARD_V3:.*?\n.*?\n(?=^[ \t]*if\s+\"db_path\"\s+in\s+params\s*:)",
    "",
    s,
    count=1,
)
# 2) SV_PATCH_RIVALRY_CHRONICLE_APPROVE_V1 blocks
s = re.sub(
    r"(?ms)^[ \t]*# SV_PATCH_RIVALRY_CHRONICLE_APPROVE_V1:.*?\n.*?\n(?=^[ \t]*if\s+\"db_path\"\s+in\s+params\s*:)",
    "",
    s,
    count=1,
)

# Anchor: just before params-branch selection in approve_latest().
m = re.search(r'(?m)^(?P<indent>[ \t]*)if\s+"db_path"\s+in\s+params\s*:\s*$', s)
if not m:
    raise SystemExit('ERROR: could not find anchor: if "db_path" in params:')

indent = m.group("indent")
insert_at = m.start()

guard = (
    f"{indent}# {SENT}\n"
    f"{indent}# Guard: never approve an empty Rivalry Chronicle. Validate the DRAFT row's rendered_text.\n"
    f"{indent}row = con.execute(\n"
    f"{indent}    \"\"\"\n"
    f"{indent}    SELECT rendered_text\n"
    f"{indent}    FROM recap_artifacts\n"
    f"{indent}    WHERE league_id = ?\n"
    f"{indent}      AND season = ?\n"
    f"{indent}      AND week_index = ?\n"
    f"{indent}      AND artifact_type = ?\n"
    f"{indent}      AND version = ?\n"
    f"{indent}      AND state = 'DRAFT'\n"
    f"{indent}    ORDER BY version DESC, id DESC\n"
    f"{indent}    LIMIT 1\n"
    f"{indent}    \"\"\",\n"
    f"{indent}    (int(req.league_id), int(req.season), int(req.week_index), str(ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1), int(draft_v)),\n"
    f"{indent}).fetchone()\n"
    f"{indent}txt = \"\" if row is None else str(row[0] or \"\")\n"
    f"{indent}if not txt.strip():\n"
    f"{indent}    raise SystemExit(\n"
    f"{indent}        \"ERROR: refusing to approve empty Rivalry Chronicle rendered_text. \"\n"
    f"{indent}        \"Re-run generate; no APPROVED stamp was applied.\"\n"
    f"{indent}    )\n\n"
)

s2 = s[:insert_at] + guard + s[insert_at:]
p.write_text(s2, encoding="utf-8")
print("OK: installed canonical approve guard (single, unconditional, deterministic).")
PY

echo "==> py_compile"
PYTHONPATH=src python -m py_compile scripts/dev_env.sh >/dev/null 2>&1 || true
PYTHONPATH=src python -m py_compile src/squadvault/consumers/rivalry_chronicle_generate_v1.py
PYTHONPATH=src python -m py_compile src/squadvault/consumers/rivalry_chronicle_approve_v1.py
echo "OK: consolidated patch v2 complete."
