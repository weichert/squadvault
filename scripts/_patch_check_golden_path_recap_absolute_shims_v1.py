from pathlib import Path
import re

p = Path("scripts/check_golden_path_recap.sh")
s = p.read_text(encoding="utf-8")

if "SCRIPT_DIR=" not in s:
    raise SystemExit("ERROR: expected SCRIPT_DIR bootstrap in check_golden_path_recap.sh")

before = s

# Ensure canonical absolute shim vars exist right after SCRIPT_DIR bootstrap.
# We insert them once, if missing.
if "PY_SHIM=" not in s and "RECAP_PY=" not in s:
    s = re.sub(
        r'(SCRIPT_DIR="\$\(\s*CDPATH=.*?\)"\s*\n)',
        r'\1'
        r'PY_SHIM="${SCRIPT_DIR}/py"\n'
        r'RECAP_PY="${SCRIPT_DIR}/recap.py"\n'
        r'RECAP_SH="${SCRIPT_DIR}/recap.sh"\n',
        s,
        count=1,
        flags=re.DOTALL,
    )

# Rewrite any remaining relative invocations to use absolute shims.
s = s.replace("./scripts/py", "${PY_SHIM}")
s = s.replace("scripts/py", "${PY_SHIM}")

s = s.replace("./scripts/recap.sh", "${RECAP_SH}")
s = s.replace("scripts/recap.sh", "${RECAP_SH}")

# If the script shells out to recap.py explicitly, make it absolute too.
s = s.replace("scripts/recap.py", "${RECAP_PY}")

# Also guard against "python -u scripts/recap.py" style.
s = s.replace("python -u ${RECAP_PY}", "${PY_SHIM} -u ${RECAP_PY}")
s = s.replace("python -u scripts/recap.py", "${PY_SHIM} -u ${RECAP_PY}")
s = s.replace("python ${RECAP_PY}", "${PY_SHIM} ${RECAP_PY}")
s = s.replace("python scripts/recap.py", "${PY_SHIM} ${RECAP_PY}")

if s == before:
    raise SystemExit("ERROR: no changes made (patterns didn’t match). Open the script and patch manually.")

p.write_text(s, encoding="utf-8")
print("OK: patched scripts/check_golden_path_recap.sh to use SCRIPT_DIR-absolute shims (PY_SHIM/RECAP_PY/RECAP_SH)")
