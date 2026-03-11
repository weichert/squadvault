from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "scripts" / "prove_creative_determinism_v1.sh"

BEGIN = "# --- SV_PRESERVE_CREATIVE_FINGERPRINT_ON_CLEAN_OUTPUTS_v1_BEGIN ---\n"
END   = "# --- SV_PRESERVE_CREATIVE_FINGERPRINT_ON_CLEAN_OUTPUTS_v1_END ---\n"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        print("OK: preserve-fingerprint clean_outputs block already present (idempotent).")
        return

    needle = '    find "${REPO_ROOT}/${root}" -type f -print0 | xargs -0 rm -f\n'
    if needle not in text:
        raise SystemExit(
            "ERROR: expected clean_outputs() removal line not found (refusing to patch).\n"
            "Look for the 'find ... -type f ... | xargs ... rm -f' line inside clean_outputs()."
        )

    block = (
        BEGIN
        + '    fingerprint_rel="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"\n'
        + '    fingerprint_abs="${REPO_ROOT}/${fingerprint_rel}"\n'
        + '\n'
        + '    # Keep directories, remove files — but preserve the tracked canonical fingerprint.\n'
        + '    if [[ "${root}" == "artifacts" ]]; then\n'
        + '      find "${REPO_ROOT}/${root}" -type f \\\n'
        + '        ! -path "${fingerprint_abs}" \\\n'
        + '        -print0 | xargs -0 rm -f\n'
        + '    else\n'
        + '      find "${REPO_ROOT}/${root}" -type f -print0 | xargs -0 rm -f\n'
        + '    fi\n'
        + END
    )

    text2 = text.replace(needle, block, 1)
    TARGET.write_text(text2, encoding="utf-8")
    print("OK: patched clean_outputs() to preserve creative fingerprint when cleaning artifacts (v1).")

if __name__ == "__main__":
    main()
