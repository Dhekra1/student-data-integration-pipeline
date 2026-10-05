"""Transformation and source-integration functions for student data."""

from datetime import datetime, timezone
from typing import Any

import pandas as pd

try:
    from .logging_config import get_logger
except ImportError:
    from logging_config import get_logger


logger = get_logger()


# ============================================================
# Data Provenance
# ============================================================


def add_provenance(
    df: pd.DataFrame,
    *,
    source: str,
    source_url: str = "local_file",
) -> pd.DataFrame:
    """Add data lineage columns to a DataFrame.


    Adds three columns:
        - source: Source label (e.g., "csv", "api", "database").
        - source_url: URL or file path describing the source.
        - retrieved_at: ISO 8601 UTC timestamp of extraction.

    Args:
        df: Input DataFrame.
        source: Source label such as "csv", "api", or "database".
        source_url: URL or file path describing the source.

    Returns:
        pd.DataFrame: A copy of the DataFrame with provenance columns added.
    """
    df = df.copy()
    df["source"] = source
    df["source_url"] = source_url
    df["retrieved_at"] = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Added provenance columns (source=%s, url=%s). Rows: %d",
        source,
        source_url,
        len(df),
    )
    return df


# ============================================================
# Private transformation helpers
# ============================================================


def _drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate student rows while retaining the first occurrence.

    Args:
        df: Student DataFrame.

    Returns:
        pd.DataFrame: DataFrame without duplicate ``student_id`` rows.
    """
    logger.info("Starting duplicate removal")
    result = df.drop_duplicates(subset=["student_id"], keep="first").copy()
    logger.info("Completed duplicate removal. Rows: %d", len(result))
    return result


def _convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert known numeric columns without changing unrelated columns.

    Args:
        df: DataFrame to normalize.

    Returns:
        pd.DataFrame: DataFrame with numeric values coerced where applicable.
    """
    logger.info("Starting numeric conversion")
    result = df.copy()
    for column in ("age", "gpa", "attendance", "course_id", "credit_hours", "score"):
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    logger.info("Completed numeric conversion")
    return result


def _apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Set invalid analytical values to missing according to requested rules.

    Args:
        df: DataFrame with numeric columns.

    Returns:
        pd.DataFrame: DataFrame with out-of-range values replaced by ``NA``.
    """
    logger.info("Starting business-rule validation")
    result = df.copy()
    for column, lower, upper in (
        ("age", 16, 80),
        ("gpa", 0.0, 4.0),
        ("attendance", 0, 100),
    ):
        if column in result.columns:
            result.loc[~result[column].between(lower, upper), column] = pd.NA
    logger.info("Completed business-rule validation")
    return result


def _impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Impute numeric missing values with each column median.

    Args:
        df: DataFrame containing numeric columns.

    Returns:
        pd.DataFrame: DataFrame with median-imputed numeric values.
    """
    logger.info("Starting missing-value imputation")
    result = df.copy()
    for column in ("age", "gpa", "attendance"):
        if column in result.columns and result[column].notna().any():
            result[column] = result[column].fillna(result[column].median())
    logger.info("Completed missing-value imputation")
    return result


# ============================================================
# Public transformation entry points
# ============================================================


def transform_students(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    apply_business_rules: bool = True,
    impute_missing: bool = True,
) -> pd.DataFrame:
    """Transform student data using configurable normalization steps.

    Args:
        df: Student DataFrame to transform.
        drop_duplicates: Whether to keep only the first ``student_id`` row.
        apply_business_rules: Whether to apply age, GPA, and attendance ranges.
        impute_missing: Whether to median-impute numeric missing values.

    Returns:
        pd.DataFrame: Transformed student DataFrame.
    """
    logger.info("Starting student transformation. Rows: %d", len(df))
    result = _convert_numeric(df)
    if drop_duplicates:
        result = _drop_duplicates(result)
    if apply_business_rules:
        result = _apply_business_rules(result)
    if impute_missing:
        result = _impute_missing(result)
    logger.info("Completed student transformation. Rows: %d", len(result))
    return result


def integrate_students(
    valid_students: list[dict[str, Any]],
    api_data: list[dict[str, Any]],
    database_data: list[tuple[Any, ...]],
    *,
    add_lineage: bool = True,
) -> pd.DataFrame:

    logger.info("Starting legacy-compatible source integration")
    student_df = transform_students(
        pd.DataFrame(valid_students),
        drop_duplicates=True,
        apply_business_rules=True,
        impute_missing=True,
    )
    api_df = pd.DataFrame(api_data)
    if not api_df.empty:
        api_df = api_df.copy()
        for column in ("student_id", "age", "attendance", "gpa"):
            if column in api_df.columns:
                api_df[column] = pd.to_numeric(api_df[column], errors="coerce")
    database_df = pd.DataFrame(
        database_data,
        columns=[
            "student_id",
            "course_id",
            "course_name",
            "credit_hours",
            "semester",
            "score",
        ],
    )
    if not database_df.empty:
        for column in ("student_id", "course_id", "credit_hours", "score"):
            if column in database_df.columns:
                database_df[column] = pd.to_numeric(
                    database_df[column], errors="coerce"
                )

    merged_df = pd.merge(student_df, api_df, on="student_id", how="left")
    final_df = pd.merge(merged_df, database_df, on="student_id", how="left")

    for column in ("age", "attendance", "course_id", "credit_hours"):
        if column in final_df.columns:
            final_df[column] = final_df[column].astype("Int64")
    for column in ("name", "email", "status", "course_name", "semester"):
        if column in final_df.columns:
            final_df[column] = final_df[column].fillna("").astype(str).str.strip()
    for column in ("gpa", "score"):
        if column in final_df.columns:
            final_df[column] = pd.to_numeric(final_df[column], errors="coerce")

    # Preserve one-to-many enrollment rows while keeping the student record itself clean.
    final_df = final_df.sort_values(["student_id", "course_id"]).reset_index(drop=True)

    # ============================================================
    # Data Provenance (Unit 7 - pages 77-78)
    # ============================================================
    if add_lineage:
        final_df["source"] = "csv+api+database"
        final_df["source_url"] = "multi-source"
        final_df["retrieved_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Added provenance columns to integrated dataset")

    final_df = _fill_enrichment_defaults(final_df)

    logger.info(
        "Completed legacy-compatible source integration. Rows: %d", len(final_df)
    )
    return final_df


def _fill_enrichment_defaults(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # Numeric defaults
    if "gpa" in df.columns:
        df["gpa"] = df["gpa"].fillna(0.0)
    if "attendance" in df.columns:
        df["attendance"] = df["attendance"].fillna(0.0)
    if "score" in df.columns:
        df["score"] = df["score"].fillna(0.0)
    if "credit_hours" in df.columns:
        df["credit_hours"] = df["credit_hours"].fillna(0)

    # Text defaults
    if "status" in df.columns:
        df["status"] = df["status"].fillna("Unknown")
    if "course_name" in df.columns:
        df["course_name"] = df["course_name"].fillna("Not Enrolled")
    if "semester" in df.columns:
        df["semester"] = df["semester"].fillna("N/A")

    logger.info("Applied default values for enrichment fields.")
    return df
