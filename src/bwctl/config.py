"""Configuration management for bwctl."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="BWCTL_DB_",
    )

    host: str = "localhost"
    port: int = 5432
    name: str = "bwctl"
    user: str = "bwctl"
    password: str = "bwctl"

    @property
    def dsn(self) -> str:
        """Get the database connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class OSCSettings(BaseSettings):
    """OSC bridge settings."""

    send_host: str = "127.0.0.1"
    send_port: int = 8000
    receive_port: int = 9000


class BitwigSettings(BaseSettings):
    """Bitwig-related settings."""

    content_paths: list[str] = Field(default_factory=lambda: [
        str(Path.home() / "Library/Application Support/Bitwig/Bitwig Studio/installed-packages"),
        str(Path.home() / "Documents/Bitwig Studio/Library"),
    ])


class SearchSettings(BaseSettings):
    """Search settings."""

    default_limit: int = 20
    fuzzy_threshold: float = 0.3


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="BWCTL_",
        env_nested_delimiter="__",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    osc: OSCSettings = Field(default_factory=OSCSettings)
    bitwig: BitwigSettings = Field(default_factory=BitwigSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)


def get_config_path() -> Path:
    """Get the configuration file path."""
    config_dir = Path.home() / ".config" / "bwctl"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"


def load_settings() -> Settings:
    """Load settings from config file and environment."""
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path) as f:
            config_data: dict[str, Any] = yaml.safe_load(f) or {}
        return Settings(**config_data)

    return Settings()


# Global settings instance
settings = load_settings()
