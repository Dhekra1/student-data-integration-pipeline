

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scraper import (  # noqa: E402
    _clean_text,
    _parse_gpa,
    _parse_student_id,
    parse_students_table,
    read_html_from_file,
    scrape_students_from_html,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_html() -> str:
    """Minimal valid student HTML."""
    return """
    <html><body>
    <table id="students">
        <thead>
            <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>City</th>
                <th>GPA</th>
                <th>Skills</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>3001</td>
                <td>Test Student A</td>
                <td>Sanaa</td>
                <td>3.50</td>
                <td>Python, SQL</td>
            </tr>
            <tr>
                <td>3002</td>
                <td>Test Student B</td>
                <td>Aden</td>
                <td>3.80</td>
                <td>Java</td>
            </tr>
        </tbody>
    </table>
    </body></html>
    """


@pytest.fixture
def sample_html_file(tmp_path, sample_html):
    """Write sample HTML to a temporary file."""
    file_path = tmp_path / "students.html"
    file_path.write_text(sample_html, encoding="utf-8")
    return file_path


# ============================================================
# File reading tests
# ============================================================

def test_read_html_from_file(sample_html_file):
    """Test reading HTML from a file."""
    html = read_html_from_file(sample_html_file)
    assert isinstance(html, str)
    assert "<table" in html
    assert "Test Student A" in html


def test_file_not_found_raises(tmp_path):
    """Test that missing files raise FileNotFoundError."""
    missing = tmp_path / "does_not_exist.html"
    with pytest.raises(FileNotFoundError):
        read_html_from_file(missing)


# ============================================================
# Parsing tests
# ============================================================

def test_parse_students_table(sample_html):
    """Test parsing the students table."""
    records = parse_students_table(sample_html)
    assert len(records) == 2
    assert records[0]["student_id"] == 3001
    assert records[0]["name"] == "Test Student A"
    assert records[0]["city"] == "Sanaa"
    assert records[0]["gpa"] == 3.50
    assert records[0]["skills"] == "Python, SQL"


def test_parse_empty_table_raises():
    """Test that HTML without a table raises ValueError."""
    html = "<html><body><p>No table here</p></body></html>"
    with pytest.raises(ValueError, match="No <table>"):
        parse_students_table(html)


# ============================================================
# Scraping tests
# ============================================================

def test_scrape_returns_dataframe(sample_html_file):
    """Test that scraping returns a valid DataFrame."""
    df = scrape_students_from_html(sample_html_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_scrape_columns(sample_html_file):
    """Test that the scraped DataFrame has the expected columns."""
    df = scrape_students_from_html(sample_html_file)
    expected = {"student_id", "name", "city", "gpa", "skills"}
    assert expected.issubset(set(df.columns))


def test_scrape_data_types(sample_html_file):
    """Test that numeric fields are correctly typed."""
    df = scrape_students_from_html(sample_html_file)
    assert df["student_id"].dtype in ("int64", "Int64")
    assert df["gpa"].dtype in ("float64", "Float64")


# ============================================================
# Helper function tests
# ============================================================

def test_clean_text():
    """Test text cleaning."""
    assert _clean_text("  hello  ") == "hello"
    assert _clean_text("") is None
    assert _clean_text("   ") is None
    assert _clean_text(None) is None


def test_parse_gpa_valid():
    """Test valid GPA parsing."""
    assert _parse_gpa("3.50") == 3.50
    assert _parse_gpa("4") == 4.0
    assert _parse_gpa("0.0") == 0.0


def test_parse_gpa_invalid():
    """Test invalid GPA parsing returns None."""
    assert _parse_gpa("N/A") is None
    assert _parse_gpa("") is None
    assert _parse_gpa(None) is None
    assert _parse_gpa("abc") is None


def test_parse_student_id():
    """Test student ID parsing."""
    assert _parse_student_id("3001") == 3001
    assert _parse_student_id("  42  ") == 42
    assert _parse_student_id("abc") is None
    assert _parse_student_id(None) is None


# ============================================================
# Integration test
# ============================================================

def test_scraped_data_is_exportable(sample_html_file, tmp_path):
    """Test that scraped data can be saved to CSV."""
    df = scrape_students_from_html(sample_html_file)
    output = tmp_path / "scraped.csv"
    df.to_csv(output, index=False)

    assert output.exists()
    reloaded = pd.read_csv(output)
    assert len(reloaded) == 2