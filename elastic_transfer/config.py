"""Load and validate environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

REQUIRED_VARS = (
    "ELASTICSEARCH_URL_ORIGIN",
    "ELASTICSEARCH_USERNAME_ORIGIN",
    "ELASTICSEARCH_PASSWORD_ORIGIN",
    "ELASTICSEARCH_URL_DESTINATION",
    "ELASTICSEARCH_USERNAME_DESTINATION",
    "ELASTICSEARCH_PASSWORD_DESTINATION",
)


@dataclass(frozen=True)
class ClusterConfig:
    url: str
    username: str
    password: str


@dataclass(frozen=True)
class AppConfig:
    origin: ClusterConfig
    destination: ClusterConfig


def load_config(env_file: str | None = None) -> AppConfig:
    """Load cluster credentials from the environment (and optional .env file)."""
    load_dotenv(env_file)

    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {names}")

    return AppConfig(
        origin=ClusterConfig(
            url=os.environ["ELASTICSEARCH_URL_ORIGIN"],
            username=os.environ["ELASTICSEARCH_USERNAME_ORIGIN"],
            password=os.environ["ELASTICSEARCH_PASSWORD_ORIGIN"],
        ),
        destination=ClusterConfig(
            url=os.environ["ELASTICSEARCH_URL_DESTINATION"],
            username=os.environ["ELASTICSEARCH_USERNAME_DESTINATION"],
            password=os.environ["ELASTICSEARCH_PASSWORD_DESTINATION"],
        ),
    )
