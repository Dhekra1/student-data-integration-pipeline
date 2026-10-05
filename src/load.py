"""Output persistence and transaction-safe SQLite loading functions."""

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .logging_config import get_logger
except ImportError:
    from logging_config import get_logger


logger = get_logger()


def save_dataframe(df: pd.DataFrame, path: Path) -> Path:
    """Save a DataFrame to CSV.

    Args:
        df: DataFrame to persist.
        path: Destination CSV path.

    Returns:
        Path: Written CSV path.
    """
    output_path = Path(path)
    logger.info("Starting CSV save to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Completed CSV save. Rows: %d", len(df))
    return output_path


def save_rejected_records(records: list[dict[str, Any]], path: Path) -> Path:
    """Save rejected validation records with their error messages.

    Args:
        records: Rejected student records and associated errors.
        path: Destination rejected-record CSV path.

    Returns:
        Path: Written rejected-record CSV path.
    """
    logger.info("Starting rejected-record save")
    rows: list[dict[str, Any]] = []
    for record in records:
        row = dict(record["student"])
        row["errors"] = "; ".join(record["errors"])
        rows.append(row)
    output_path = save_dataframe(pd.DataFrame(rows), path)
    logger.info("Completed rejected-record save. Rows: %d", len(rows))
    return output_path


def _create_students_schema(connection: sqlite3.Connection, table_name: str) -> None:
    """Create the analysis-ready students table if it does not exist.

    Args:
        connection: Open SQLite connection.
        table_name: Target SQLite table name.

    Raises:
        ValueError: If the requested table name is not the supported table.
    """
    if table_name != "students":
        raise ValueError("Only the students table is supported")

    required_columns = {
        "student_id": "INTEGER",
        "name": "TEXT",
        "age": "INTEGER",
        "email": "TEXT",
        "phone": "TEXT",
        "gpa": "REAL",
        "attendance": "INTEGER",
        "status": "TEXT",
        "course_id": "INTEGER",
        "course_name": "TEXT",
        "credit_hours": "INTEGER",
        "semester": "TEXT",
        "score": "REAL",
        "source": "TEXT",
        "source_url": "TEXT",
        "retrieved_at": "TEXT",
    }

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER,
            name TEXT,
            age INTEGER,
            email TEXT,
            phone TEXT,
            gpa REAL,
            attendance INTEGER,
            status TEXT,
            course_id INTEGER,
            course_name TEXT,
            credit_hours INTEGER,
            semester TEXT,
            score REAL,
            source TEXT,
            source_url TEXT,
            retrieved_at TEXT
        )
        """)

    existing_columns = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )


def load_to_sqlite(
    df: pd.DataFrame, db_path: Path, table_name: str = "students"
) -> None:
    """Replace target SQLite student rows within an explicit transaction.

    Args:
        df: Final transformed student DataFrame.
        db_path: Destination SQLite database path.
        table_name: Destination table name; defaults to ``students``.

    Raises:
        sqlite3.Error: If SQLite cannot create or load the target table.
    """
    database_path = Path(db_path)
    logger.info("Starting SQLite load to %s", database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        _create_students_schema(connection, table_name)
        connection.execute(f"DELETE FROM {table_name}")
        df.to_sql(table_name, connection, if_exists="append", index=False)
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        logger.exception("SQLite load failed and was rolled back")
        raise
    finally:
        connection.close()
    logger.info("Completed SQLite load. Rows: %d", len(df))


def read_loaded_students(db_path: Path, table_name: str = "students") -> pd.DataFrame:
    """Read the target SQLite table for verification.

    Args:
        db_path: SQLite database path.
        table_name: SQLite table name.

    Returns:
        pd.DataFrame: Persisted student rows.

    Raises:
        FileNotFoundError: If the target database does not exist.
    """
    database_path = Path(db_path)
    logger.info("Starting SQLite load verification from %s", database_path)
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")
    with sqlite3.connect(database_path) as connection:
        data = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
    logger.info("Completed SQLite load verification. Rows: %d", len(data))
    return data
