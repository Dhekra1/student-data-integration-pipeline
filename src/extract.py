"""Extraction functions for CSV, REST API, and SQLite source data."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import requests

try:
    from .config import resolve_path
    from .logging_config import get_logger
except ImportError:
    from config import resolve_path
    from logging_config import get_logger


logger = get_logger()


# ============================================================
# CSV Extraction
# ============================================================

def extract_csv(path: Path) -> pd.DataFrame:
    """Read student records from a CSV file.

    Args:
        path: CSV file to read.

    Returns:
        pd.DataFrame: Extracted CSV records.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    source_path = Path(path)
    logger.info("Starting CSV extraction from %s", source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"CSV file not found: {source_path}")

    data = pd.read_csv(source_path)
    logger.info("Completed CSV extraction. Rows: %d", len(data))
    return data


def save_raw_copy(data: pd.DataFrame, destination: Path) -> Path:
    """Save an unmodified snapshot of extracted CSV data.

    Args:
        data: Extracted source rows to preserve.
        destination: Destination CSV path for the snapshot.

    Returns:
        Path: Written snapshot path.
    """
    output_path = Path(destination)
    logger.info("Starting raw copy save to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)
    logger.info("Completed raw copy save. Rows: %d", len(data))
    return output_path


# ============================================================
# API Extraction (Unit 7 - pages 12, 18-22, 30)
# ============================================================

def save_raw_api_response(data: list[dict[str, Any]], destination: Path) -> Path:
    """Save the raw JSON API response to disk.

    Reference: Unit 7 - page 30 (Saving the Raw Response).

    Args:
        data: The raw list of records returned by the API.
        destination: Destination JSON file path.

    Returns:
        Path: Written JSON file path.
    """
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Starting raw API response save to %s", output_path)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    logger.info("Completed raw API response save. Records: %d", len(data))
    return output_path


def extract_api(
    url: str,
    *,
    paginated: bool = False,
    max_pages: int = 100,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Retrieve student enrichment records from the configured REST API.

    Supports optional pagination (Unit 7 - pages 18-22).

    Args:
        url: API endpoint URL (base URL if ``paginated`` is True).
        paginated: Whether to fetch multiple pages using ``?page=N``.
        max_pages: Safety limit for pagination (Unit 7 - page 23).
        timeout: Request timeout in seconds.

    Returns:
        list[dict[str, Any]]: JSON API records.

    Raises:
        requests.RequestException: If the API request is unsuccessful.
        ValueError: If the API returns a non-list JSON payload.
    """
    if paginated:
        return _extract_api_paginated(url, max_pages=max_pages, timeout=timeout)
    return _extract_api_single(url, timeout=timeout)


def _extract_api_single(url: str, *, timeout: int) -> list[dict[str, Any]]:
    """Fetch a single-page API response.

    Args:
        url: API endpoint URL.
        timeout: Request timeout in seconds.

    Returns:
        list[dict[str, Any]]: JSON records.

    Raises:
        requests.RequestException: On HTTP error.
        ValueError: If payload is not a list.
    """
    logger.info("Starting API extraction from %s", url)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("API response must be a JSON list of student records")

    logger.info("Completed API extraction. Rows: %d", len(data))
    return data


def _extract_api_paginated(
    base_url: str,
    *,
    max_pages: int,
    timeout: int,
) -> list[dict[str, Any]]:
    """Fetch all pages from a paginated API endpoint.

    Reference: Unit 7 - pages 19-22.

    Args:
        base_url: Base API URL (without page parameter).
        max_pages: Safety limit (Unit 7 - page 23).
        timeout: Request timeout in seconds.

    Returns:
        list[dict[str, Any]]: Combined records from all pages.

    Raises:
        requests.RequestException: On HTTP error.
    """
    logger.info("Starting paginated API extraction from %s", base_url)
    all_records: list[dict[str, Any]] = []
    page = 1

    while page <= max_pages:
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}page={page}&limit=100"
        logger.debug("Fetching page %d: %s", page, url)

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.info("Empty page received at page %d. Stopping.", page)
            break

        if not isinstance(data, list):
            raise ValueError("API page must be a JSON list")

        all_records.extend(data)
        logger.info("Page %d returned %d records.", page, len(data))
        page += 1

    logger.info("Completed paginated API extraction. Total rows: %d", len(all_records))
    return all_records


# ============================================================
# Database Extraction
# ============================================================

def extract_database(path: Path) -> list[tuple[Any, ...]]:
    """Extract enrollment and course data from the existing source database.

    Args:
        path: SQLite source database path.

    Returns:
        list[tuple[Any, ...]]: Enrollment rows in the legacy merge order.
    """
    database_path = Path(path)
    logger.info("Starting SQLite source extraction from %s", database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    query = """
        SELECT e.student_id, e.course_id, c.course_name, c.credit_hours,
               e.semester, e.score
        FROM enrollments AS e
        JOIN courses AS c ON e.course_id = c.course_id
    """
    with sqlite3.connect(database_path) as connection:
        _ensure_source_schema(connection)
        rows = connection.execute(query).fetchall()

    logger.info("Completed SQLite source extraction. Rows: %d", len(rows))
    return rows


def _ensure_source_schema(connection: sqlite3.Connection) -> None:
    """Create and seed source course tables when they are absent."""
    logger.info("Ensuring SQLite source schema is available")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY,
            course_name TEXT NOT NULL,
            credit_hours INTEGER
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id INTEGER,
            course_id INTEGER,
            semester TEXT,
            score REAL
        )
        """
    )
    if connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO courses (course_id, course_name, credit_hours) VALUES (?, ?, ?)",
            [
                (1, "Python Programming", 3),
                (2, "Database Systems", 3),
                (3, "Artificial Intelligence", 4),
            ],
        )
    if connection.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO enrollments (student_id, course_id, semester, score) VALUES (?, ?, ?, ?)",
            [
                (1001, 1, "2026-1", 88),
                (1001, 2, "2026-1", 91),
                (1002, 1, "2026-1", 95),
                (1002, 3, "2026-1", 89),
                (1003, 2, "2026-1", 72),
                (1004, 1, "2026-1", 84),
            ],
        )
    connection.commit()
    logger.info("SQLite source schema is ready")


# ============================================================
# Orchestration
# ============================================================

def extract_all(
    config: dict[str, Any],
) -> tuple[list[tuple[Any, ...]], pd.DataFrame, list[dict[str, Any]]]:
    """Extract all source datasets using runtime configuration.

    Saves:
        - Raw CSV snapshot to ``data/raw/students_raw_backup.csv``.
        - Raw API response to ``data/raw/api_response.json`` (Unit 7 - page 30).

    Args:
        config: Runtime configuration dictionary.

    Returns:
        tuple: Database rows, CSV records, and API records.
    """
    logger.info("Starting extraction from all configured sources")
    paths = config["paths"]

    # 1. Database
    database_data = extract_database(resolve_path(paths["source_database"]))

    # 2. CSV
    csv_data = extract_csv(resolve_path(paths["raw_data"]))

    # Save raw CSV snapshot
    save_raw_copy(csv_data, resolve_path(paths["staging_data"]))

    # 3. API
    api_data = extract_api(str(config["api_url"]))

    # Save raw API response (Unit 7 - page 30)
    raw_api_path = resolve_path(paths["raw_data"]).parent / "api_response.json"
    save_raw_api_response(api_data, raw_api_path)

    logger.info("Completed extraction from all configured sources")
    return database_data, csv_data, api_data