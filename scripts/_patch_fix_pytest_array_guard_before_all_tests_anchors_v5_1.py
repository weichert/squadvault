from __future__ import annotations
from pathlib import Path

REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
ANCHOR = "pytest target must start with Tests/"
SIG = 'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"'
ARRAY_RE = r"^['\"']*\$\{[A-Za-z0-9_]+_tests\[@\]\}['\"']*$"

GUARD = (
  'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"\n'
  'if [ -n "${sv_tok-}" ] && echo "${sv_tok-}" | '
  "grep -Eq '" + ARRAY_RE + "' ; then\n"
  "  continue\n"
  "fi\n"
)

def _root() -> Path:
  return Path(__file__).resolve().parents[1]
def main() -> int:
  p = _root() / REL
  if not p.exists():
    raise SystemExit(f"ERROR: missing {REL}")
  s = p.read_text(encoding="utf-8")
  if ANCHOR not in s:
    raise SystemExit(f"ERROR: anchor not found in {REL} (refusing).")

  lines = s.splitlines(keepends=True)
  out: list[str] = []
  ins = 0
  for i, ln in enumerate(lines):
    if ANCHOR in ln:
      window = "".join(lines[max(0, i-20):i])
      if SIG not in window:
        out.append(GUARD); ins += 1
    out.append(ln)

  if ins == 0:
    print("OK: guard already present before all Tests/ anchors (noop).")
    return 0
  p.write_text("".join(out), encoding="utf-8")
  print(f"OK: inserted guard before {ins} Tests/ anchor(s) (v5.1).")
  return 0
if __name__ == "__main__":
  raise SystemExit(main())
