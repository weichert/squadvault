set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
t="${repo_root}/scripts/patch_writing_room_signal_grouping_v1_intake_fix.sh"

if [[ ! -f "$t" ]]; then
  echo "ERROR: missing $t"
  exit 1
fi

first="$(head -n 1 "$t" || true)"
if [[ "$first" == "#!"* ]]; then
  echo "OK: shebang already present; no change."
  exit 0
fi

tmp="$(mktemp)"
{
  echo '#!/usr/bin/env bash'
  cat "$t"
} > "$tmp"

mv "$tmp" "$t"
chmod +x "$t"

echo "OK: added shebang to scripts/patch_writing_room_signal_grouping_v1_intake_fix.sh"
echo "Next:"
echo "  bash -x ./scripts/patch_writing_room_signal_grouping_v1_intake_fix.sh"
