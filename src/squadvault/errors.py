"""SquadVault error hierarchy.

Business logic raises these; CLI main() functions catch and convert to SystemExit.
"""
from __future__ import annotations


class SquadVaultError(Exception):
    """Base error for all SquadVault business logic failures."""
    pass


class RecapNotFoundError(SquadVaultError):
    """A required recap or artifact was not found."""
    pass


class RecapStateError(SquadVaultError):
    """A recap or artifact is in an invalid state for the requested operation."""
    pass


class RecapDataError(SquadVaultError):
    """Data required for recap generation is missing, invalid, or inconsistent."""
    pass


class ChronicleError(SquadVaultError):
    """Error in chronicle generation, persistence, or export."""
    pass


class ConfigError(SquadVaultError):
    """Missing or invalid configuration (env vars, paths, etc.)."""
    pass


class SchemaError(SquadVaultError):
    """Database schema is missing required tables or columns."""
    pass
