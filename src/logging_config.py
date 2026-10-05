"""
Logging configuration for the AI Data Pipeline.

This module sets up a centralized logger that writes to both:
    1. A log file (logs/pipeline.log)
    2. Standard output (console)

Usage:
    from logging_config import setup_logging
    logger = setup_logging()
    logger.info("Pipeline started.")
"""

import logging
import sys
from pathlib import Path


# ===== Default Configuration =====
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = logging.INFO


def setup_logging(
    log_file: Path = DEFAULT_LOG_FILE,
    level: int = DEFAULT_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Configure and return the pipeline logger.

    Args:
        log_file: Path to the log file. Defaults to logs/pipeline.log.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_to_file: Whether to write logs to a file.
        log_to_console: Whether to print logs to the console.

    Returns:
        logging.Logger: Configured logger instance named "pipeline".
    """
    logger = logging.getLogger("pipeline")

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    if log_to_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False

    logger.info("Logging configured. Log file: %s", log_file)
    return logger


def get_logger() -> logging.Logger:
    """
    Retrieve the pipeline logger.

    If the logger has not been configured yet, it will be set up with
    default settings.

    Returns:
        logging.Logger: The pipeline logger.
    """
    logger = logging.getLogger("pipeline")
    if not logger.handlers:
        return setup_logging()
    return logger