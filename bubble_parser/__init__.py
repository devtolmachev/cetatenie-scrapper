"""Bubble parser. Api for parser and postgres database."""
from __future__ import annotations

from envyaml import EnvYAML


def get_config(path: str | None = None) -> EnvYAML:
    """Get dict with config values."""
    if not path:
        path = "config.yml"
        
    return EnvYAML(
        yaml_file=path,
        env_file=".env",
        include_environment=False,
        flatten=False,
    )
