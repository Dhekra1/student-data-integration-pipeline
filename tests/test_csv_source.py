from pathlib import Path

from src.extract import extract_csv


def test_csv_loaded():
    data = extract_csv(Path("data/raw/students.csv"))

    assert data is not None
    assert len(data) > 0
    assert {"student_id", "name", "age", "email", "phone"}.issubset(data.columns)