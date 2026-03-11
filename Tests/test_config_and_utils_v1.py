"""Tests for config/settings and utils/time.

Covers: SquadVaultConfig.from_env, unix_seconds_to_iso_z.
"""
from __future__ import annotations

import os

import pytest

from squadvault.config.settings import SquadVaultConfig
from squadvault.utils.time import unix_seconds_to_iso_z


class TestSquadVaultConfig:
    def test_default_values(self):
        """Config has sensible defaults."""
        cfg = SquadVaultConfig()
        assert cfg.db_path == ".local_squadvault.sqlite"
        assert cfg.season == 2024
        assert cfg.debug is False
        assert cfg.league_id is None

    def test_from_env(self, monkeypatch):
        """from_env reads environment variables."""
        monkeypatch.setenv("SQUADVAULT_DB", "/tmp/test.db")
        monkeypatch.setenv("MFL_LEAGUE_ID", "70985")
        monkeypatch.setenv("SQUADVAULT_YEAR", "2023")
        monkeypatch.setenv("SV_DEBUG", "1")
        cfg = SquadVaultConfig.from_env()
        assert cfg.db_path == "/tmp/test.db"
        assert cfg.league_id == "70985"
        assert cfg.season == 2023
        assert cfg.debug is True

    def test_from_env_defaults(self, monkeypatch):
        """from_env uses defaults when env vars are not set."""
        monkeypatch.delenv("SQUADVAULT_DB", raising=False)
        monkeypatch.delenv("MFL_LEAGUE_ID", raising=False)
        monkeypatch.delenv("SQUADVAULT_YEAR", raising=False)
        monkeypatch.delenv("SV_DEBUG", raising=False)
        cfg = SquadVaultConfig.from_env()
        assert cfg.db_path == ".local_squadvault.sqlite"
        assert cfg.debug is False

    def test_frozen(self):
        """Config is immutable."""
        cfg = SquadVaultConfig()
        with pytest.raises(AttributeError):
            cfg.db_path = "something_else"

    def test_db_path_resolved(self):
        """db_path_resolved returns a Path."""
        cfg = SquadVaultConfig(db_path="test.db")
        assert cfg.db_path_resolved.name == "test.db"


class TestUnixSecondsToIsoZ:
    def test_epoch(self):
        """Unix epoch converts to 1970-01-01."""
        result = unix_seconds_to_iso_z(0)
        assert result == "1970-01-01T00:00:00Z"

    def test_known_timestamp(self):
        """Known timestamp converts correctly."""
        # 2024-01-01 00:00:00 UTC = 1704067200
        result = unix_seconds_to_iso_z(1704067200)
        assert result is not None
        assert result.startswith("2024-01-01")
        assert result.endswith("Z")

    def test_none_returns_none(self):
        """None input returns None."""
        assert unix_seconds_to_iso_z(None) is None
