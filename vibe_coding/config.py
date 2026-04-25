from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

CONFIG_PATH = Path("config.yaml")
ENV_PATH = Path(".env")


def load_config() -> dict[str, Any]:
    """Load configuration from config.yaml and .env files.

    Returns:
        Dictionary with configuration values.

    Raises:
        FileNotFoundError: If config.yaml is not found.
    """
    load_dotenv(ENV_PATH)

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open() as f:
        config: dict[str, Any] = yaml.safe_load(f)

    return config


def get_twitch_oauth() -> str:
    """Get Twitch OAuth token from environment.

    Returns:
        OAuth token string.

    Raises:
        ValueError: If token not found in environment.
    """
    import os

    token = os.getenv("TWITCH_OAUTH_TOKEN")
    if not token:
        raise ValueError("TWITCH_OAUTH_TOKEN not found in .env")
    return token


def get_twitch_nick() -> str:
    """Get Twitch username from environment.

    Returns:
        Username string.

    Raises:
        ValueError: If username not found in environment.
    """
    import os

    nick = os.getenv("TWITCH_NICK")
    if not nick:
        raise ValueError("TWITCH_NICK not found in .env")
    return nick


CONFIG: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """Get cached configuration, loading if necessary.

    Returns:
        Configuration dictionary.
    """
    global CONFIG
    if CONFIG is None:
        CONFIG = load_config()
    return CONFIG