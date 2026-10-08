"""Shared fixtures. RNG seeds are fixed; tests must not require Binance data."""

from __future__ import annotations

from pathlib import Path

import pytest

from exec_impact import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def config() -> dict:
    return load_config()


@pytest.fixture(scope="session")
def seed(config: dict) -> int:
    return int(config["seed"])
