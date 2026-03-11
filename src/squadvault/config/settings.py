"""SquadVault configuration management.

Centralizes environment variable access with defaults and validation.
All config is read-only after initialization.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SquadVaultConfig:
    """Immutable configuration loaded from environment variables."""

    db_path: str = ".local_squadvault.sqlite"
    league_id: Optional[str] = None
    season: int = 2024
    debug: bool = False

    @classmethod
    def from_env(cls) -> SquadVaultConfig:
        """Load configuration from environment variables.

        Recognized variables:
            SQUADVAULT_DB       — path to SQLite database
            MFL_LEAGUE_ID       — league identifier
            SQUADVAULT_YEAR     — season year
            SV_DEBUG            — set to "1" for debug output
        """
        return cls(
            db_path=os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"),
            league_id=os.environ.get("MFL_LEAGUE_ID"),
            season=int(os.environ.get("SQUADVAULT_YEAR", "2024")),
            debug=os.environ.get("SV_DEBUG") == "1",
        )

    @property
    def db_path_resolved(self) -> Path:
        """Return db_path as a resolved Path."""
        return Path(self.db_path).resolve()
