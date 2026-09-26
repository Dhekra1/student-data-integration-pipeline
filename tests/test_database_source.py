from app.sources.database_source import extract_database


def test_sqlite_extracted():

    data = extract_database("database/students.db")

    assert data is not None
    assert len(data) > 0