"""Validation functions for raw CSV records and final student datasets."""

import re
from typing import Any

import pandas as pd

try:
    from .logging_config import get_logger
except ImportError:
    from logging_config import get_logger


logger = get_logger()
REQUIRED_COLUMNS = ("student_id", "name", "age", "email", "phone")
EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def validate_student_record(student: dict[str, Any]) -> list[str]:
    """Validate one CSV student record using the existing business rules.

    Args:
        student: Raw student record.

    Returns:
        list[str]: Validation messages; an empty list means the record is valid.
    """
    errors: list[str] = []
    if not student.get("student_id"):
        errors.append("student_id is required")
    if not student.get("name"):
        errors.append("name is required")

    age = student.get("age")
    if pd.isna(age):
        errors.append("age is required")
    elif not isinstance(age, int):
        errors.append("age must be an integer")
    elif age < 16 or age > 100:
        errors.append("age must be between 16 and 100")

    email = student.get("email")
    if not email:
        errors.append("email is required")
    elif not EMAIL_PATTERN.match(str(email)):
        errors.append("email format is invalid")

    phone = student.get("phone")
    if not phone:
        errors.append("phone is required")
    else:
        normalized_phone = str(phone)
        if not normalized_phone.isdigit():
            errors.append("phone must contain only digits")
        elif not 9 <= len(normalized_phone) <= 15:
            errors.append("phone must contain between 9 and 15 digits")
    return errors


def validate_csv_data(data: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split raw CSV rows into valid records and rejected records.

    Args:
        data: Raw CSV student DataFrame.

    Returns:
        tuple: Valid student dictionaries and rejected record dictionaries.
    """
    logger.info("Starting CSV record validation. Rows: %d", len(data))
    valid_students: list[dict[str, Any]] = []
    rejected_students: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()

    for _, row in data.iterrows():
        student = row.to_dict()
        student_id = student.get("student_id")
        if student_id in seen_ids:
            rejected_students.append({"student": student, "errors": ["duplicate student_id"]})
            continue
        seen_ids.add(student_id)

        if pd.notna(student.get("age")):
            student["age"] = int(student["age"])
        errors = validate_student_record(student)
        if errors:
            rejected_students.append({"student": student, "errors": errors})
        else:
            valid_students.append(student)

    logger.info("Completed CSV validation. Valid: %d; rejected: %d", len(valid_students), len(rejected_students))
    return valid_students, rejected_students


def validate_students(
    df: pd.DataFrame,
    allow_duplicate_student_ids: bool = False,
    allow_enrichment_nulls: bool = False,
) -> None:
    """Validate a final student DataFrame and raise on invalid data.

    Args:
        df: Final student DataFrame.
        allow_duplicate_student_ids: Allow duplicate IDs for one-to-many enrollment rows.
        allow_enrichment_nulls: Allow missing API/enrollment fields after left joins.

    Raises:
        ValueError: If required columns, values, uniqueness, or ranges are invalid.
    """
    logger.info("Starting final student validation. Rows: %d", len(df))
    errors: list[str] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    else:
        for column in REQUIRED_COLUMNS:
            if df[column].isna().any() or df[column].astype(str).str.strip().eq("").any():
                errors.append(f"{column} contains missing or empty values")
        if not allow_duplicate_student_ids and df["student_id"].duplicated().any():
            errors.append("student_id must be unique")
        if not df["age"].between(16, 80).all():
            errors.append("age must be between 16 and 80")

    if not allow_enrichment_nulls:
        for column, lower, upper in (("gpa", 0.0, 4.0), ("attendance", 0, 100)):
            if column in df.columns:
                if df[column].isna().any() or not df[column].between(lower, upper).all():
                    errors.append(f"{column} must be between {lower} and {upper} with no missing values")

    if errors:
        logger.error("Final student validation failed: %s", "; ".join(errors))
        raise ValueError("; ".join(errors))
    logger.info("Completed final student validation successfully")