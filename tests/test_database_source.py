from pathlib import Path

from src.extract import extract_database


def test_sqlite_extracted():
    data = extract_database(Path("data/processed/students.db"))

    assert data is not None
    assert len(data) > 0
    assert len(data[0]) == 6