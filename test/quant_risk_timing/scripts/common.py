"""Shared script helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_config(config_path: str | Path | None = None) -> dict:
    """Load the project YAML configuration."""

    path = Path(config_path) if config_path else PROJECT_ROOT / "config" / "config.yaml"
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def resolve_project_path(path_value: str) -> Path:
    """Resolve a config path relative to the project root."""

    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path
