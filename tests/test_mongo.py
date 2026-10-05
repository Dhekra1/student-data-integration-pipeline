

import sys
from pathlib import Path

import pandas as pd
import pytest
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from config import load_config  # noqa: E402
from mongo_loader import (  # noqa: E402
    aggregate_avg_gpa_by_status,
    count_documents,
    create_indexes,
    get_mongo_client,
    load_from_mongo,
    save_to_mongo,
)


# ============================================================
# Pytest fixtures
# ============================================================

@pytest.fixture(scope="module")
def mongo_config() -> dict:
    """Load and validate MongoDB configuration from .env."""
    cfg = load_config()
    mongo = cfg["mongo"]

    if not mongo.get("enabled", False):
        pytest.skip("MongoDB is disabled (MONGO_ENABLED=false).")

    return mongo


@pytest.fixture(scope="module")
def mongo_client(mongo_config):
    """Create a MongoDB client for the whole test session."""
    client = get_mongo_client(
        mongo_config["uri"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    yield client
    client.close()


@pytest.fixture(autouse=True)
def clean_collection(mongo_client, mongo_config):
    """Drop the target collection before each test.

    Ensures every test starts from a clean state.
    """
    collection = mongo_client[mongo_config["db_name"]][mongo_config["collection"]]
    collection.drop()

    yield

    collection.drop()


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small, realistic sample dataset."""
    return pd.DataFrame(
        [
            {
                "student_id": 1001, "name": "Ahmed Ali", "age": 21,
                "gpa": 3.45, "attendance": 92.0, "status": "Active",
                "course_id": 1, "course_name": "Python Programming",
                "credit_hours": 3, "semester": "2026-1", "score": 88.0,
                "source": "test", "source_url": "test",
                "retrieved_at": "2026-10-05T00:00:00+00:00",
            },
            {
                "student_id": 1001, "name": "Ahmed Ali", "age": 21,
                "gpa": 3.45, "attendance": 92.0, "status": "Active",
                "course_id": 2, "course_name": "Database Systems",
                "credit_hours": 3, "semester": "2026-1", "score": 91.0,
                "source": "test", "source_url": "test",
                "retrieved_at": "2026-10-05T00:00:00+00:00",
            },
            {
                "student_id": 1002, "name": "Sara Mohammed", "age": 22,
                "gpa": 3.80, "attendance": 88.0, "status": "Active",
                "course_id": 1, "course_name": "Python Programming",
                "credit_hours": 3, "semester": "2026-1", "score": 95.0,
                "source": "test", "source_url": "test",
                "retrieved_at": "2026-10-05T00:00:00+00:00",
            },
        ]
    )


# ============================================================
# Tests
# ============================================================

def test_connection_works(mongo_config):
    """Test that MongoDB is reachable (Unit 8 — pages 29-30)."""
    client = get_mongo_client(
        mongo_config["uri"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert client.admin.command("ping")["ok"] == 1.0
    client.close()


def test_save_and_count(mongo_config, sample_df):
    """Test that saving records increases the collection count."""
    written = save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert written == 3

    total = count_documents(
        mongo_config["uri"],
        mongo_config["db_name"],
        mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert total == 3


def test_idempotency(mongo_config, sample_df):
    """Re-running the save should NOT duplicate documents (Unit 8 — pages 35-36)."""
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )

    total = count_documents(
        mongo_config["uri"],
        mongo_config["db_name"],
        mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert total == 3, "Idempotency failed: duplicates were created."


def test_load_to_dataframe(mongo_config, sample_df):
    """Test reading documents back into a Pandas DataFrame (Unit 8 — pages 37-38)."""
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )

    df = load_from_mongo(
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "student_id" in df.columns
    assert "course_id" in df.columns
    assert set(df["student_id"]) == {1001, 1002}


def test_load_with_query(mongo_config, sample_df):
    """Test MongoDB filtering (Unit 8 — pages 15-16)."""
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )

    df = load_from_mongo(
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
        query={"student_id": 1002},
    )
    assert len(df) == 1
    assert df.iloc[0]["name"] == "Sara Mohammed"


def test_aggregation_avg_gpa(mongo_config, sample_df):
    """Test the Aggregation Pipeline (Unit 8 — pages 50-51)."""
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )

    df = aggregate_avg_gpa_by_status(
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert not df.empty
    assert "status" in df.columns
    assert "average_gpa" in df.columns
    # Expected average: (3.45 + 3.45 + 3.80) / 3 = 3.5666...
    avg = df.iloc[0]["average_gpa"]
    assert abs(avg - 3.5667) < 0.01


def test_unique_index_prevents_duplicates(mongo_config):
    """Test that the compound unique index works (Unit 8 — pages 49-50)."""
    client = MongoClient(mongo_config["uri"])
    collection = client[mongo_config["db_name"]][mongo_config["collection"]]

    try:
        create_indexes(collection)

        doc = {
            "student_id": 9999,
            "course_id": 42,
            "name": "Test Student",
        }
        collection.insert_one(doc)

        # Try to insert the same (student_id, course_id) → should fail
        with pytest.raises(DuplicateKeyError):
            collection.insert_one(doc)
    finally:
        client.close()


def test_provenance_fields_preserved(mongo_config, sample_df):
    """Test that provenance columns are stored in MongoDB."""
    save_to_mongo(
        df=sample_df,
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )

    df = load_from_mongo(
        uri=mongo_config["uri"],
        db_name=mongo_config["db_name"],
        collection_name=mongo_config["collection"],
        timeout_ms=mongo_config["timeout_ms"],
    )
    assert "source" in df.columns
    assert "source_url" in df.columns
    assert "retrieved_at" in df.columns


def test_empty_dataframe_raises(mongo_config):
    """Test that saving an empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError, match="empty"):
        save_to_mongo(
            df=empty_df,
            uri=mongo_config["uri"],
            db_name=mongo_config["db_name"],
            collection_name=mongo_config["collection"],
            timeout_ms=mongo_config["timeout_ms"],
        )