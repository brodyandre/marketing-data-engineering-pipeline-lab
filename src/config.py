from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "samples"
DEFAULT_POSTGRES_SCHEMA = "analytics"


class ConfigError(RuntimeError):
    """Raised when required configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    project_root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    sample_data_dir: Path
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_schema: str

    @property
    def sqlalchemy_url(self) -> str:
        # Local default credentials are intentionally non-sensitive placeholders.
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def psycopg_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def _resolve_path(value: str, base: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def _read_env(name: str, default: str, legacy_name: str | None = None) -> str:
    """Read value from current env name, optionally falling back to a legacy alias."""
    if value := os.getenv(name):
        return value
    if legacy_name and (legacy := os.getenv(legacy_name)):
        return legacy
    return default


def _read_port() -> int:
    raw_port = _read_env("POSTGRES_PORT", "5432", legacy_name="DB_PORT")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ConfigError(
            f"Invalid POSTGRES_PORT value '{raw_port}'. Expected an integer."
        ) from exc

    if port <= 0 or port > 65535:
        raise ConfigError(
            f"Invalid POSTGRES_PORT value '{raw_port}'. Expected range 1-65535."
        )
    return port


def get_settings() -> Settings:
    # Load .env if present; otherwise use process environment with safe local defaults.
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    else:
        load_dotenv()

    project_root = _resolve_path(
        os.getenv("PROJECT_ROOT", str(PROJECT_ROOT)),
        PROJECT_ROOT,
    )

    raw_data_dir = _resolve_path(
        os.getenv("RAW_DATA_DIR", str(DEFAULT_RAW_DATA_DIR)),
        project_root,
    )
    processed_data_dir = _resolve_path(
        os.getenv("PROCESSED_DATA_DIR", str(DEFAULT_PROCESSED_DATA_DIR)),
        project_root,
    )
    sample_data_dir = _resolve_path(
        os.getenv("SAMPLE_DATA_DIR", str(DEFAULT_SAMPLE_DATA_DIR)),
        project_root,
    )

    return Settings(
        project_root=project_root,
        raw_data_dir=raw_data_dir,
        processed_data_dir=processed_data_dir,
        sample_data_dir=sample_data_dir,
        db_host=_read_env("POSTGRES_HOST", "localhost", legacy_name="DB_HOST"),
        db_port=_read_port(),
        db_name=_read_env("POSTGRES_DB", "marketing_dw", legacy_name="DB_NAME"),
        db_user=_read_env("POSTGRES_USER", "postgres", legacy_name="DB_USER"),
        # Default password is intentionally generic for local/dev only.
        db_password=_read_env(
            "POSTGRES_PASSWORD",
            "postgres",
            legacy_name="DB_PASSWORD",
        ),
        db_schema=_read_env(
            "POSTGRES_SCHEMA",
            DEFAULT_POSTGRES_SCHEMA,
            legacy_name="DB_SCHEMA",
        ),
    )


def ensure_directories(settings: Settings) -> None:
    """Create required local data directories if they do not exist."""
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
