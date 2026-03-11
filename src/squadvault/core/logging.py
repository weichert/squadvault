"""SquadVault structured logging.

Provides a consistent logging interface with SV_DEBUG support.
Debug output is opt-in via SV_DEBUG=1 environment variable.
Default behavior: quiet unless there is a problem.
"""
from __future__ import annotations

import logging
import os
import sys


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _is_debug() -> bool:
    """Return True if SV_DEBUG=1 is set."""
    return os.environ.get("SV_DEBUG") == "1"


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name.

    Respects SV_DEBUG=1 for verbose output.
    Default level is WARNING (quiet unless something is wrong).
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT))
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG if _is_debug() else logging.WARNING)
    return logger
