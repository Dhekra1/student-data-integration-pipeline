import logging
from pathlib import Path


LOG_FILE = Path("logs/pipeline.log")

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger("pipeline")

if __name__ == "__main__":

    logger.info("Logger test: pipeline logging is working.")

    print("Log test completed.")