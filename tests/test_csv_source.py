from app.sources.csv_source import extract_csv


def test_csv_loaded():

    data = extract_csv("data/raw/students.csv")

    assert data is not None
    assert len(data) > 0