from pathlib import Path
from typing import Iterable, Tuple

from scripts.ingest.garmin_sleep import ingest_sleep
from scripts.ingest.garmin_health_status import ingest_health_status
from scripts.ingest.garmin_uds import ingest_uds

from scripts.compute_daily_features import compute_daily_features_for_user
from backend.run_inference import run_inference_for_user


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def partition_garmin_files(files: Iterable[Path]) -> Tuple[list[Path], list[Path], list[Path]]:
    """
    Split Garmin JSON files into their respective ingestion buckets.
    """
    sleep: list[Path] = []
    health: list[Path] = []
    uds: list[Path] = []

    for path in files:
        name = path.name

        if name.endswith("sleepData.json"):
            sleep.append(path)
        elif name.endswith("healthStatusData.json"):
            health.append(path)
        elif name.startswith("UDSFile_"):
            uds.append(path)

    return sleep, health, uds


# ─────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────

def process_garmin_upload(
    *,
    user_id: str,
    files: Iterable[Path],
) -> dict:
    """
    End-to-end Garmin ingestion pipeline for a single user.

    Steps:
      1. Ingest raw Garmin JSON files
      2. Compute daily features
      3. Run mood inference

    Returns:
      {
        "days_ingested": int,
        "days_predicted": int
      }
    """

    files = list(files)
    if not files:
        return {
            "days_ingested": 0,
            "days_predicted": 0,
        }

    # 1️⃣ Partition files
    sleep_files, health_files, uds_files = partition_garmin_files(files)

    # 2️⃣ Ingest
    if sleep_files:
        ingest_sleep(sleep_files, user_id)

    if health_files:
        ingest_health_status(health_files, user_id)

    if uds_files:
        ingest_uds(uds_files, user_id)

    # 3️⃣ Compute features
    compute_daily_features_for_user(user_id)

    # 4️⃣ Run inference
    days_predicted = run_inference_for_user(user_id)

    return {
        "days_ingested": len(files),
        "days_predicted": days_predicted,
    }
