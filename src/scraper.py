"""
Web Scraping layer — Semi-structured data acquisition from HTML.

This module implements the Web Scraping pipeline stage (Unit 7):
    1. Fetch or read HTML content.
    2. Parse it with BeautifulSoup.
    3. Extract tabular data.
    4. Normalize and clean the extracted fields.
    5. Return a Pandas DataFrame.

Reference: Unit 7 — Web Scraping (Pages 42-63).

Usage:
    from scraper import scrape_students_from_html, scrape_students_from_url
    df = scrape_students_from_html(Path("data/raw/web_students.html"))
"""

from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from .logging_config import get_logger
except ImportError:
    from logging_config import get_logger


logger = get_logger()


# ============================================================
# Configuration (Unit 7 — page 55)
# ============================================================

DEFAULT_USER_AGENT = "StudentDataPipeline/1.0 (Educational)"
DEFAULT_TIMEOUT = 10


# ============================================================
# Internal helpers
# ============================================================

def _clean_text(value: str | None) -> str | None:
    """Strip whitespace and normalize empty strings to None.

    Args:
        value: Raw text extracted from HTML.

    Returns:
        str | None: Cleaned text or None if empty.
    """
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _parse_gpa(value: str | None) -> float | None:
    """Parse a GPA value, returning None on failure.

    Reference: Unit 7 — pages 52-53 (Converting Numeric Values).

    Args:
        value: Raw text.

    Returns:
        float | None: Parsed GPA or None if invalid.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_student_id(value: str | None) -> int | None:
    """Parse a student ID, returning None on failure.

    Args:
        value: Raw text.

    Returns:
        int | None: Parsed ID or None if invalid.
    """
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# HTML Fetching (Unit 7 — pages 46-50)
# ============================================================

def fetch_html_from_url(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> str:
    """Fetch raw HTML from a URL using Requests.

    Reference: Unit 7 — pages 46, 55 (User-Agent).

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        user_agent: User-Agent header identifying the client.

    Returns:
        str: Raw HTML content.

    Raises:
        requests.RequestException: On network or HTTP errors.
    """
    logger.info("Fetching HTML from URL: %s", url)
    headers = {"User-Agent": user_agent}

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    logger.info(
        "Fetched %d bytes from %s (status %d).",
        len(response.text), url, response.status_code,
    )
    return response.text


def read_html_from_file(file_path: Path) -> str:
    """Read raw HTML from a local file.

    Args:
        file_path: Path to the HTML file.

    Returns:
        str: Raw HTML content.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {path}")

    logger.info("Reading HTML from file: %s", path)
    html = path.read_text(encoding="utf-8")
    logger.info("Read %d characters from %s.", len(html), path)
    return html


# ============================================================
# HTML Parsing (Unit 7 — pages 47-51)
# ============================================================

def parse_students_table(html: str) -> list[dict[str, Any]]:
    """Parse a student table from raw HTML.

    Expected table structure:
        <table id="students">
            <thead>
                <tr><th>Student ID</th><th>Name</th>...</tr>
            </thead>
            <tbody>
                <tr><td>2001</td><td>Ali Hassan</td>...</tr>
            </tbody>
        </table>

    Reference: Unit 7 — pages 45-51.

    Args:
        html: Raw HTML content.

    Returns:
        list[dict[str, Any]]: Parsed records.

    Raises:
        ValueError: If the students table is not found.
    """
    logger.info("Parsing students table from HTML.")
    soup = BeautifulSoup(html, "lxml")

    # Find the table (by id first, fallback to first table)
    table = soup.find("table", id="students") or soup.find("table")
    if table is None:
        raise ValueError("No <table> element found in the HTML.")

    # Read headers
    headers = [
        _clean_text(th.get_text())
        for th in table.select("thead th")
    ]
    if not headers:
        # Fallback: infer from first row
        first_row = table.find("tr")
        if first_row:
            headers = [_clean_text(td.get_text()) for td in first_row.find_all(["th", "td"])]

    logger.debug("Detected headers: %s", headers)

    # Parse rows
    records: list[dict[str, Any]] = []
    for row in table.select("tbody tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        values = [_clean_text(cell.get_text()) for cell in cells]

        # Skip rows that don't have enough cells
        if len(values) < 2:
            logger.warning("Skipping malformed row: %s", values)
            continue

        record = {
            "student_id": _parse_student_id(values[0]) if len(values) > 0 else None,
            "name": values[1] if len(values) > 1 else None,
            "city": values[2] if len(values) > 2 else None,
            "gpa": _parse_gpa(values[3]) if len(values) > 3 else None,
            "skills": values[4] if len(values) > 4 else None,
        }
        records.append(record)

    logger.info("Parsed %d student record(s).", len(records))
    return records


# ============================================================
# Public API
# ============================================================

def scrape_students_from_html(file_path: Path) -> pd.DataFrame:
    """Scrape student data from a local HTML file.

    Args:
        file_path: Path to the HTML file.

    Returns:
        pd.DataFrame: Scraped records with provenance columns.
    """
    html = read_html_from_file(file_path)
    records = parse_students_table(html)

    if not records:
        raise ValueError("No student records were scraped from the HTML.")

    df = pd.DataFrame(records)
    logger.info("Scraped DataFrame shape: %s", df.shape)
    return df


def scrape_students_from_url(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> pd.DataFrame:
    """Scrape student data from a remote URL.

    Reference: Unit 7 — pages 45-63.

    Args:
        url: The URL to fetch and scrape.
        timeout: Request timeout in seconds.
        user_agent: User-Agent header.

    Returns:
        pd.DataFrame: Scraped records.
    """
    html = fetch_html_from_url(url, timeout=timeout, user_agent=user_agent)
    records = parse_students_table(html)

    if not records:
        raise ValueError(f"No student records found at {url}.")

    df = pd.DataFrame(records)
    logger.info("Scraped DataFrame shape: %s", df.shape)
    return df


# ============================================================
# Manual test
# ============================================================

if __name__ == "__main__":
    """Quick manual test:

        cd src
        python scraper.py
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    html_file = Path("../data/raw/web_students.html")

    print("\n=== Web Scraping Test ===")
    try:
        df = scrape_students_from_html(html_file)
        print(f"\nRows scraped: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print("\nData:")
        print(df.to_string(index=False))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Failed: {exc}")
        sys.exit(1)