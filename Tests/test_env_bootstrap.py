"""Tests for scripts/_env_bootstrap.py.

The bootstrap module lives under ``scripts/`` rather than ``src/``,
so it is not on the normal package path. We load it by file location
via ``importlib`` to keep the test hermetic — no ``sys.path`` mutation,
no cross-test contamination.

The load-bearing invariant under test is "does not overwrite a key
already present in ``os.environ``" — the load_dotenv-at-import-time
anti-pattern's primary failure mode is silently shadowing
shell-exported values, and this bootstrap was specifically designed
to avoid it.
"""
from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BOOTSTRAP_PATH = _REPO_ROOT / "scripts" / "_env_bootstrap.py"

# Test-only env keys; the clean_env fixture pops these before and after
# each test so direct assignments inside bootstrap_env_local don't leak.
_TEST_KEYS: tuple[str, ...] = (
    "SV_BOOTSTRAP_TEST_KEY_A",
    "SV_BOOTSTRAP_TEST_KEY_B",
)


def _load_bootstrap_module():
    spec = importlib.util.spec_from_file_location(
        "_env_bootstrap_under_test", _BOOTSTRAP_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def bootstrap_fn():
    """Fresh module load per test (importlib bypasses sys.modules cache)."""
    return _load_bootstrap_module().bootstrap_env_local


@pytest.fixture()
def clean_env() -> Iterator[None]:
    """Pop test-only keys before and after each test.

    bootstrap_env_local writes directly to os.environ, which monkeypatch
    does not track. Explicit pop here avoids cross-test leak.
    """
    saved = {k: os.environ.get(k) for k in _TEST_KEYS}
    for k in _TEST_KEYS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k in _TEST_KEYS:
            os.environ.pop(k, None)
            if saved[k] is not None:
                os.environ[k] = saved[k]


def test_silent_when_file_missing(tmp_path, bootstrap_fn, clean_env):
    """If the env file does not exist, do not raise and do not write env."""
    missing = tmp_path / "does_not_exist.env"
    assert not missing.exists()

    bootstrap_fn(env_path=missing)   # must not raise

    for k in _TEST_KEYS:
        assert k not in os.environ


def test_populates_missing_key(tmp_path, bootstrap_fn, clean_env):
    """A key absent from os.environ but present in the file is populated."""
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "SV_BOOTSTRAP_TEST_KEY_A=alpha\n"
        "SV_BOOTSTRAP_TEST_KEY_B=beta\n",
        encoding="utf-8",
    )

    bootstrap_fn(env_path=env_file)

    assert os.environ["SV_BOOTSTRAP_TEST_KEY_A"] == "alpha"
    assert os.environ["SV_BOOTSTRAP_TEST_KEY_B"] == "beta"


def test_does_not_overwrite_shell_set_value(tmp_path, bootstrap_fn, clean_env):
    """Shell-exported values take precedence; bootstrap MUST NOT shadow them.

    This is the load-bearing test. The whole point of this module's
    design is to avoid the load_dotenv anti-pattern where library
    code silently shadows user-set environment variables.
    """
    os.environ["SV_BOOTSTRAP_TEST_KEY_A"] = "from_shell"
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "SV_BOOTSTRAP_TEST_KEY_A=from_file\n"
        "SV_BOOTSTRAP_TEST_KEY_B=also_from_file\n",
        encoding="utf-8",
    )

    bootstrap_fn(env_path=env_file)

    # Shell value preserved.
    assert os.environ["SV_BOOTSTRAP_TEST_KEY_A"] == "from_shell"
    # Unset key still gets populated from the file.
    assert os.environ["SV_BOOTSTRAP_TEST_KEY_B"] == "also_from_file"


def test_strips_matched_surrounding_quotes(tmp_path, bootstrap_fn, clean_env):
    """Values wrapped in matched single or double quotes have them stripped."""
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        'SV_BOOTSTRAP_TEST_KEY_A="double_quoted_value"\n'
        "SV_BOOTSTRAP_TEST_KEY_B='single_quoted_value'\n",
        encoding="utf-8",
    )

    bootstrap_fn(env_path=env_file)

    assert os.environ["SV_BOOTSTRAP_TEST_KEY_A"] == "double_quoted_value"
    assert os.environ["SV_BOOTSTRAP_TEST_KEY_B"] == "single_quoted_value"


def test_ignores_blanks_comments_and_malformed_lines(
    tmp_path, bootstrap_fn, clean_env
):
    """Blanks, comment lines, and lines without '=' are skipped silently."""
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "\n"
        "# This is a comment\n"
        "   # indented comment\n"
        "this_line_has_no_equals_sign\n"
        "SV_BOOTSTRAP_TEST_KEY_A=alpha\n"
        "\n"
        "SV_BOOTSTRAP_TEST_KEY_B=beta\n",
        encoding="utf-8",
    )

    bootstrap_fn(env_path=env_file)

    assert os.environ["SV_BOOTSTRAP_TEST_KEY_A"] == "alpha"
    assert os.environ["SV_BOOTSTRAP_TEST_KEY_B"] == "beta"
