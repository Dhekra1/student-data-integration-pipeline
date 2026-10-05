import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MOCK_API_DATA = [
    {"student_id": 1001, "gpa": 3.45, "attendance": 92, "status": "Active"},
    {"student_id": 1002, "gpa": 3.80, "attendance": 88, "status": "Active"},
    {"student_id": 1003, "gpa": 2.70, "attendance": 65, "status": "Active"},
    {"student_id": 1004, "gpa": 3.20, "attendance": 78, "status": "Active"},
]


class MockApiResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return MOCK_API_DATA


@pytest.fixture(autouse=True)
def mock_api_requests(monkeypatch):
    """Mock the HTTP boundary so tests do not require a running Flask server."""
    monkeypatch.setattr("requests.get", lambda url, **kwargs: MockApiResponse())
