from __future__ import annotations

from pathlib import Path
import re

PROVE = Path("scripts/prove_ci.sh")

# Replace only common forms:
#   bash "$REPO_ROOT/scripts/foo.sh"
#   bash $REPO_ROOT/scripts/foo.sh
#   bash "$REPO_ROOT/scripts/foo"
# -> bash scripts/foo(.sh)
PAT = re.compile(
    r'(^[ \t]*bash[ \t]+)"?\$REPO_ROOT/scripts/([^"\s]+)"?([ \t]*)(#.*)?$',
    re.M,
)

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")

    def repl(m: re.Match[str]) -> str:
        head = m.group(1)
        path = m.group(2)
        tail_ws = m.group(3) or ""
        comment = m.group(4) or ""
        return f'{head}scripts/{path}{tail_ws}{comment}'

    new = PAT.sub(repl, text)

    if new == text:
        print("OK: prove_ci has no REPO_ROOT-based bash scripts invocations (noop)")
        return

    PROVE.write_text(new, encoding="utf-8")
    print("OK: prove_ci REPO_ROOT-based bash scripts invocations normalized (v1)")

if __name__ == "__main__":
    main()
