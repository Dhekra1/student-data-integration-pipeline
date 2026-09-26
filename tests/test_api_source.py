from app.sources.api_source import extract_api


def test_api_connected():

    data = extract_api("http://127.0.0.1:5000/students")

    assert data is not None
    assert len(data) > 0