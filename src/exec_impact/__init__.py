"""Estimate crypto market impact and compare Almgren-Chriss, TWAP, and VWAP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

__version__ = "0.1.0"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the research YAML config."""
    config_path = path or DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        msg = f"config at {config_path} must be a mapping"
        raise TypeError(msg)
    return loaded
