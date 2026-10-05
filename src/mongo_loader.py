"""
MongoDB loader — semi-structured student data.

This module handles the MongoDB integration stage of the pipeline:
    1. Connect to a local or remote MongoDB instance.
    2. Store the integrated student dataset as documents.
    3. Create a unique index on student_id (idempotency).
    4. Read documents back as a Pandas DataFrame.
    5. Provide aggregation helpers for reporting.

Reference: Unit 8 — MongoDB & NoSQL (Pages 29-38, 47-51).

Usage:
    from mongo_loader import (
        get_mongo_client, save_to_mongo, load_from_mongo,
        aggregate_avg_gpa_by_status, create_indexes,
    )
"""

from typing import Any

import pandas as pd
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

try:
    from .logging_config import get_logger
except ImportError:
    from logging_config import get_logger


logger = get_logger()


# ============================================================
# Connection Management 
# ============================================================


def get_mongo_client(
    uri: str,
    timeout_ms: int = 5000,
) -> MongoClient:
   
    logger.info("Connecting to MongoDB at %s", uri)
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command("ping")
        logger.info("MongoDB connection successful.")
        return client
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError(
            f"MongoDB connection timed out: {uri}. " f"Is the MongoDB service running?"
        ) from exc
    except ConnectionFailure as exc:
        raise RuntimeError(f"MongoDB connection failed: {exc}") from exc
    except OperationFailure as exc:
        raise RuntimeError(f"MongoDB authentication failed: {exc}") from exc


def get_collection(
    uri: str,
    db_name: str,
    collection_name: str,
    timeout_ms: int = 5000,
) -> tuple[MongoClient, Collection]:
    """Return a client and collection handle.

    MongoDB creates the database and collection lazily on first write.

    Args:
        uri: MongoDB connection string.
        db_name: Target database name.
        collection_name: Target collection name.
        timeout_ms: Server selection timeout in milliseconds.

    Returns:
        tuple: (MongoClient, Collection)
    """
    client = get_mongo_client(uri, timeout_ms=timeout_ms)
    collection = client[db_name][collection_name]
    logger.info("Using MongoDB collection: %s.%s", db_name, collection_name)
    return client, collection


# ============================================================
# Indexes 
# ============================================================


def create_indexes(collection: Collection) -> None:
    
    logger.info("Creating compound unique index on (student_id, course_id)")

    # Drop the old single-field index if it exists
    try:
        collection.drop_index("uniq_student_id")
        logger.info("Dropped old 'uniq_student_id' index.")
    except Exception:
        pass  # Index didn't exist — fine

    collection.create_index(
        [("student_id", ASCENDING), ("course_id", ASCENDING)],
        unique=True,
        name="uniq_student_course",
    )
    logger.info("Index 'uniq_student_course' ensured.")

# ============================================================
# Write Operations 
# ============================================================


def save_to_mongo(
    df: pd.DataFrame,
    uri: str,
    db_name: str,
    collection_name: str,
    timeout_ms: int = 5000,
    replace_existing: bool = True,
) -> int:
    
    if df.empty:
        raise ValueError("Cannot save an empty DataFrame to MongoDB.")

    client, collection = get_collection(
        uri, db_name, collection_name, timeout_ms=timeout_ms
    )

    try:
        # Unique index for idempotency (Unit 8 — pages 49-50)
        create_indexes(collection)

        # Convert NaN → None (MongoDB cannot store NaN reliably)
        records = df.where(pd.notna(df), None).to_dict(orient="records")

        if replace_existing:
            # Upsert each record by student_id + course_id + semester
            written = 0
            for record in records:
                # Use student_id as the upsert key to match the unique index
                # created by `create_indexes`. Using course-level fields in the
                # filter could cause MongoDB to attempt inserting a second
                # document for the same `student_id` (different course_id),
                # which violates the unique constraint and raises
                # DuplicateKeyError. Keep the upsert/filter aligned with the
                # index for idempotency.
                filter_key = {
                    "student_id": record.get("student_id"),
                    "course_id": record.get("course_id"),
                }
                result = collection.update_one(
                    filter_key, {"$set": record}, upsert=True
                )
                if result.upserted_id is not None or result.modified_count > 0:
                    written += 1
            logger.info(
                "Upserted %d documents into %s.%s", written, db_name, collection_name
            )
        else:
            result = collection.insert_many(records)
            written = len(result.inserted_ids)
            logger.info(
                "Inserted %d documents into %s.%s", written, db_name, collection_name
            )

        return written

    except Exception as exc:
        logger.exception("MongoDB write failed: %s", exc)
        raise RuntimeError(f"MongoDB write failed: {exc}") from exc
    finally:
        client.close()


# ============================================================
# Read Operations (Unit 8 — Pages 15-17, 37-38)
# ============================================================


def load_from_mongo(
    uri: str,
    db_name: str,
    collection_name: str,
    timeout_ms: int = 5000,
    query: dict[str, Any] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load MongoDB documents into a Pandas DataFrame.

    Nested documents are flattened using ``pd.json_normalize``
    (Unit 8 — pages 37-38).

    Args:
        uri: MongoDB connection string.
        db_name: Source database name.
        collection_name: Source collection name.
        timeout_ms: Server selection timeout in milliseconds.
        query: Optional MongoDB filter.
        limit: Optional limit on returned documents.

    Returns:
        pd.DataFrame: Flat DataFrame of documents.
    """
    client, collection = get_collection(
        uri, db_name, collection_name, timeout_ms=timeout_ms
    )

    try:
        filter_query = query or {}
        cursor = collection.find(filter_query, {"_id": 0})
        if limit:
            cursor = cursor.limit(limit)

        records = list(cursor)
        logger.info(
            "Loaded %d documents from %s.%s", len(records), db_name, collection_name
        )

        if not records:
            return pd.DataFrame()

        df = pd.json_normalize(records)
        return df
    finally:
        client.close()


# ============================================================
# Aggregation (Unit 8 — Pages 50-51)
# ============================================================


def aggregate_avg_gpa_by_status(
    uri: str,
    db_name: str,
    collection_name: str,
    timeout_ms: int = 5000,
) -> pd.DataFrame:
    """Compute average GPA grouped by student status.

    Reference: Unit 8 — pages 50-51 (Aggregation Pipeline).

    Args:
        uri: MongoDB connection string.
        db_name: Database name.
        collection_name: Collection name.
        timeout_ms: Server selection timeout.

    Returns:
        pd.DataFrame: Columns ``status`` and ``average_gpa``.
    """
    client, collection = get_collection(
        uri, db_name, collection_name, timeout_ms=timeout_ms
    )

    try:
        pipeline = [
            {"$match": {"gpa": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$status",
                    "average_gpa": {"$avg": "$gpa"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"average_gpa": -1}},
        ]
        results = list(collection.aggregate(pipeline))
        logger.info("Aggregation returned %d groups.", len(results))

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results).rename(columns={"_id": "status"})
        return df
    finally:
        client.close()


def count_documents(
    uri: str,
    db_name: str,
    collection_name: str,
    timeout_ms: int = 5000,
) -> int:
    """Return the number of documents in a collection.

    Args:
        uri: MongoDB connection string.
        db_name: Database name.
        collection_name: Collection name.
        timeout_ms: Server selection timeout.

    Returns:
        int: Document count.
    """
    client, collection = get_collection(
        uri, db_name, collection_name, timeout_ms=timeout_ms
    )
    try:
        return collection.count_documents({})
    finally:
        client.close()


# ============================================================
# Manual test
# ============================================================

if __name__ == "__main__":
    """Quick manual test:

    cd src
    python mongo_loader.py
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from config import load_config

    cfg = load_config()
    mongo_cfg = cfg["mongo"]

    print("\n=== MongoDB Configuration ===")
    print(f"Enabled : {mongo_cfg['enabled']}")
    print(f"URI     : {mongo_cfg['uri']}")
    print(f"DB      : {mongo_cfg['db_name']}")
    print(f"Coll    : {mongo_cfg['collection']}")

    if not mongo_cfg["enabled"]:
        print("\nMongoDB is disabled. Set MONGO_ENABLED=true in .env")
        sys.exit(0)

    try:
        count = count_documents(
            mongo_cfg["uri"],
            mongo_cfg["db_name"],
            mongo_cfg["collection"],
            timeout_ms=mongo_cfg["timeout_ms"],
        )
        print(f"\nCurrent document count: {count}")
    except RuntimeError as exc:
        print(f"\nConnection failed: {exc}")
        sys.exit(1)
