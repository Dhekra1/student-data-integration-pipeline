"""Single executable entry point for the refactored student data pipeline."""

import uuid
from pathlib import Path

import pandas as pd

if __package__:
    from .config import PROJECT_ROOT, load_config, resolve_path
    from .extract import extract_all, save_raw_copy
    from .load import load_to_sqlite, save_dataframe, save_rejected_records
    from .logging_config import get_logger
    from .mongo_loader import count_documents, save_to_mongo
    from .scraper import scrape_students_from_html
    from .transform import integrate_students
    from .validate import validate_csv_data, validate_students
else:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import PROJECT_ROOT, load_config, resolve_path
    from extract import extract_all, save_raw_copy
    from load import load_to_sqlite, save_dataframe, save_rejected_records
    from logging_config import get_logger
    from mongo_loader import count_documents, save_to_mongo
    from scraper import scrape_students_from_html
    from transform import integrate_students
    from validate import validate_csv_data, validate_students


logger = get_logger()


def _load_to_mongodb(final_df: pd.DataFrame, config: dict) -> None:
    """Load the final dataset into MongoDB when enabled.

    Reference: Unit 8 — MongoDB & NoSQL (Pages 29-38).

    If ``MONGO_ENABLED=true`` in the environment, this function upserts
    every record into the configured MongoDB collection. Failures are
    logged but do NOT stop the pipeline (MongoDB is optional).

    Args:
        final_df: Final integrated DataFrame.
        config: Runtime configuration containing a ``mongo`` section.
    """
    mongo_cfg = config.get("mongo", {})

    if not mongo_cfg.get("enabled", False):
        logger.info("MongoDB load skipped (MONGO_ENABLED=false).")
        return

    try:
        logger.info(
            "Starting MongoDB load. URI: %s | DB: %s | Collection: %s",
            mongo_cfg["uri"],
            mongo_cfg["db_name"],
            mongo_cfg["collection"],
        )

        written = save_to_mongo(
            df=final_df,
            uri=mongo_cfg["uri"],
            db_name=mongo_cfg["db_name"],
            collection_name=mongo_cfg["collection"],
            timeout_ms=mongo_cfg["timeout_ms"],
            replace_existing=True,
        )
        total = count_documents(
            uri=mongo_cfg["uri"],
            db_name=mongo_cfg["db_name"],
            collection_name=mongo_cfg["collection"],
            timeout_ms=mongo_cfg["timeout_ms"],
        )
        logger.info(
            "MongoDB load completed. Documents written: %d | Total in collection: %d",
            written,
            total,
        )
        print(f"MongoDB load completed. Documents written: {written}")

    except Exception as exc:
        # MongoDB is optional — log and continue
        logger.exception("MongoDB load failed: %s", exc)
        print(f"MongoDB load failed (pipeline continues): {exc}")


def _scrape_web_data(config: dict) -> None:
    """Scrape web data from a local HTML file (Unit 7 — Web Scraping).

    Reference: Unit 7 — pages 45-63.

    Saves the scraped DataFrame to ``data/processed/web_students.csv``.
    Failures are logged but do NOT stop the pipeline.

    Args:
        config: Runtime configuration.
    """
    paths = config["paths"]
    html_file = resolve_path(paths.get("web_html", "data/raw/web_students.html"))

    if not html_file.exists():
        logger.warning("Web HTML file not found: %s. Skipping scrape.", html_file)
        print(f"Web Scraping skipped (file not found: {html_file}).")
        return

    try:
        logger.info("Starting Web Scraping from %s", html_file)
        web_df = scrape_students_from_html(html_file)

        # Add provenance (Unit 7 — pages 77-78)
        web_df["source"] = "web_scraping"
        web_df["source_url"] = str(html_file)
        from datetime import datetime, timezone
        web_df["retrieved_at"] = datetime.now(timezone.utc).isoformat()

        output_path = resolve_path(
            paths.get("web_students", "data/processed/web_students.csv")
        )
        save_dataframe(web_df, output_path)

        logger.info(
            "Web Scraping completed. Rows: %d | Saved to: %s",
            len(web_df), output_path,
        )
        print(f"Web Scraping completed. Rows: {len(web_df)}")

    except Exception as exc:
        logger.exception("Web Scraping failed: %s", exc)
        print(f"Web Scraping failed (pipeline continues): {exc}")


def run_pipeline() -> pd.DataFrame:
    """Run extraction, validation, integration, output, and loading stages.

    Returns:
        pd.DataFrame: Final integrated student DataFrame.

    Raises:
        Exception: Re-raises any pipeline failure after logging it.
    """
    batch_id = uuid.uuid4().hex
    logger.info("Starting pipeline batch %s", batch_id)
    try:
        config = load_config()
        paths = config["paths"]
        database_data, csv_data, api_data = extract_all(config)
        print("Extract completed successfully.")

        save_raw_copy(csv_data, resolve_path(paths["raw_backup"]))
        save_raw_copy(csv_data, resolve_path(paths["staging_data"]))

        valid_students, rejected_students = validate_csv_data(csv_data)
        print("Validation completed successfully.")
        save_dataframe(pd.DataFrame(valid_students), resolve_path(paths["valid_students"]))
        save_rejected_records(rejected_students, resolve_path(paths["rejected_records"]))
        print("Validation results saved successfully.")

        final_df = integrate_students(valid_students, api_data, database_data)
        print("Transformation completed successfully.")
        print(final_df)

        validate_students(
            final_df,
            allow_duplicate_student_ids=True,
            allow_enrichment_nulls=True,
        )
        print("Final validation completed successfully.")
        output_path = save_dataframe(final_df, resolve_path(paths["final_dataset"]))
        print(f"Final dataset saved to: {output_path.relative_to(PROJECT_ROOT)}")

        # ===== SQLite Load =====
        load_to_sqlite(
            final_df,
            resolve_path(paths["database"]),
            str(config["database"]["table_name"]),
        )
        print("SQLite load completed successfully.")

        # ===== MongoDB Load (Unit 8) =====
        _load_to_mongodb(final_df, config)

        # ===== Web Scraping (Unit 7) =====
        _scrape_web_data(config)

        logger.info("Pipeline batch %s completed successfully", batch_id)
        return final_df
    except Exception:
        logger.exception("Pipeline batch %s failed", batch_id)
        raise


def main() -> None:
    """Execute the pipeline from the command line.

    Raises:
        Exception: Re-raises failures after they are logged by ``run_pipeline``.
    """
    run_pipeline()


if __name__ == "__main__":
    main()