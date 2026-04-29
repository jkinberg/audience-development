"""Cloud Run entry point: sync state from GCS, run pipeline, sync state back."""

import os
import logging
from pathlib import Path

from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cloud_run")

BUCKET_NAME = os.getenv("GCS_BUCKET", "audience-development-agents-state")

STATE_FILES = [
    "data/digest_history.json",
    "data/reshare_log.json",
    "data/reshare_candidates.json",
    "config/watchlist.json",
]


def download_state():
    """Download state files from GCS before pipeline run."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    for filepath in STATE_FILES:
        blob = bucket.blob(filepath)
        local_path = Path(filepath)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if blob.exists():
            blob.download_to_filename(str(local_path))
            logger.info(f"Downloaded {filepath} from gs://{BUCKET_NAME}/{filepath}")
        else:
            logger.info(f"No existing {filepath} in GCS — starting fresh")


def upload_state():
    """Upload state files to GCS after pipeline run."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    for filepath in STATE_FILES:
        local_path = Path(filepath)
        if local_path.exists():
            blob = bucket.blob(filepath)
            blob.upload_from_filename(str(local_path))
            logger.info(f"Uploaded {filepath} to gs://{BUCKET_NAME}/{filepath}")


def main():
    # Ensure data and output directories exist
    Path("data/runs").mkdir(parents=True, exist_ok=True)
    Path("output/digests").mkdir(parents=True, exist_ok=True)

    # Download state from GCS
    logger.info("=== Downloading state from GCS ===")
    download_state()

    # Run the pipeline
    logger.info("=== Running pipeline ===")
    os.environ["PYTHONPATH"] = "."
    from scripts.run_pipeline import main as run_pipeline
    run_pipeline()

    # Upload state back to GCS
    logger.info("=== Uploading state to GCS ===")
    upload_state()

    logger.info("=== Cloud Run job complete ===")


if __name__ == "__main__":
    main()
