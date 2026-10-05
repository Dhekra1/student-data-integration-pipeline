"""Configuration loading for the student data integration pipeline."""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:

    def load_dotenv(dotenv_path: Path | None = None, **kwargs) -> bool:
        """Provide a no-op fallback when python-dotenv is unavailable.

        Accepts arbitrary kwargs so callers can pass `override=True` safely
        when the real ``python-dotenv`` is installed.

        Args:
            dotenv_path: Optional environment-file path retained for API
                compatibility with ``python-dotenv``.

        Returns:
            bool: Always ``False`` because no environment file was loaded.
        """
        return False


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "api_url": "http://127.0.0.1:5000/students",
    "paths": {
        "raw_data": "data/raw/students.csv",
        "raw_backup": "data/raw/students_raw_backup.csv",
        "staging_data": "data/staging/extracted_students.csv",
        "valid_students": "data/processed/valid_students.csv",
        "final_dataset": "data/processed/final_dataset.csv",
        "web_html": "data/raw/web_students.html",
        "web_students": "data/processed/web_students.csv",
        "rejected_records": "data/rejected/rejected_records.csv",
        "source_database": "data/processed/students.db",
        "database": "data/processed/students.db",
        "log_file": "logs/pipeline.log",
    },
    "database": {"table_name": "students"},
    "mongo": {
        "uri": "mongodb://localhost:27017/",
        "db_name": "university_ai",
        "collection": "students",
        "timeout_ms": 5000,
        "enabled": False,
    },
}


def _merge_config(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge nested configuration dictionaries.

    Args:
        base: Default configuration values.
        overrides: User-provided configuration values.

    Returns:
        dict[str, Any]: The merged configuration.
    """
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_mongo_env(config: dict[str, Any]) -> dict[str, Any]:

    mongo_cfg = config.setdefault("mongo", {})

    if uri := os.getenv("MONGO_URI"):
        mongo_cfg["uri"] = uri
    if db_name := os.getenv("MONGO_DB_NAME"):
        mongo_cfg["db_name"] = db_name
    if collection := os.getenv("MONGO_COLLECTION"):
        mongo_cfg["collection"] = collection
    if timeout := os.getenv("MONGO_TIMEOUT_MS"):
        try:
            mongo_cfg["timeout_ms"] = int(timeout)
        except ValueError:
            pass
    if enabled := os.getenv("MONGO_ENABLED"):
        mongo_cfg["enabled"] = enabled.strip().lower() in {"1", "true", "yes"}

    return config


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load defaults, an optional local JSON config, and environment overrides.

    Args:
        config_path: Optional JSON configuration file. Defaults to
            ``config/config.json`` under the project root.

    Returns:
        dict[str, Any]: Fully merged runtime configuration.

    Raises:
        ValueError: If the selected configuration file is not valid JSON.
    """
    # Prefer .env values over existing environment variables so local
    # development settings in `.env` are honored. Use `override=True`
    # when python-dotenv is available; the fallback accepts kwargs.
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    selected_path = config_path or DEFAULT_CONFIG_PATH
    config = deepcopy(DEFAULT_CONFIG)

    if selected_path.exists():
        try:
            file_config = json.loads(selected_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON configuration: {selected_path}") from exc
        config = _merge_config(config, file_config)

    # Environment overrides
    config["api_url"] = os.getenv("API_URL", config["api_url"])
    config = _load_mongo_env(config)

    return config


def resolve_path(value: str | Path) -> Path:
    """Resolve a project-relative path to an absolute ``Path``.

    Args:
        value: Relative or absolute filesystem path.

    Returns:
        Path: Absolute resolved project path.
    """
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path
