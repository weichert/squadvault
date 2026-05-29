"""scripts/_env_bootstrap.py — Idempotent .env.local loader for engine scripts.

Loads ``.env.local`` from the engine repo root into ``os.environ`` for
keys that are not already set, so scripts requiring credentials (e.g.
the Supabase sync scripts) work in any terminal without a manual
``set -a; source .env.local; set +a``.

Design rules (deliberate):
  * Pure stdlib — no python-dotenv.
  * Resolved by absolute path from this module's ``__file__``;
    CWD-independent.
  * Never overwrites a key already present in ``os.environ`` —
    shell-exported values win.
  * Silent no-op if ``.env.local`` is missing or unreadable; the
    downstream "missing key" error from the consumer keeps its
    existing clear message.
  * Called from ``main()`` only — never at module import time —
    so importing this module as a library has no side effects.

Why not python-dotenv: dotenv's default ``load_dotenv()`` searches
CWD upward, which produces shell-vs-runtime env divergence depending
on where the script is launched from. See the engine repo memo
``_observations/OBSERVATIONS_2026_05_28_LIVE_API_ASYMMETRY_AND_LOAD_DOTENV_IMPORT.md``
for the failure mode this module is designed to avoid.
"""
from __future__ import annotations

import os
from pathlib import Path

# scripts/_env_bootstrap.py lives at scripts/, one level under the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ENV_FILE = _REPO_ROOT / ".env.local"


def bootstrap_env_local(env_path: Path | None = None) -> None:
    """Populate ``os.environ`` from ``.env.local`` for keys not already set.

    Parameters
    ----------
    env_path:
        Optional override for the dotenv file location. When ``None``,
        ``<repo_root>/.env.local`` is used. Passing an explicit path is
        primarily for tests.

    Behavior
    --------
    * Returns silently if the file does not exist or cannot be read.
    * Parses bare ``KEY=VALUE`` lines; ignores blank lines and lines
      starting with ``#``.
    * Strips one matched pair of surrounding single or double quotes
      from values (so ``KEY="foo"`` yields ``foo``).
    * Skips any key already present in ``os.environ`` — the shell
      environment takes precedence.
    * Lines without ``=`` are skipped silently.
    """
    target = env_path if env_path is not None else _DEFAULT_ENV_FILE
    try:
        text = target.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip one matched pair of surrounding quotes, if present.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
