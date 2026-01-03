import json
import pprint
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

SLEEP_UPSERT_SQL = """
INSERT INTO sleep_summary (
  user_id,
  date,
  total_sleep_minutes,
  deep_sleep_minutes,
  light_sleep_minutes,
  rem_sleep_minutes,
  awake_minutes,
  sleep_score,
  bedtime,
  wake_time,
  source
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(total_sleep_minutes)s,
  %(deep_sleep_minutes)s,
  %(light_sleep_minutes)s,
  %(rem_sleep_minutes)s,
  %(awake_minutes)s,
  %(sleep_score)s,
  %(bedtime)s,
  %(wake_time)s,
  %(source)s
)
ON CONFLICT (user_id, date)
DO UPDATE SET
  total_sleep_minutes = EXCLUDED.total_sleep_minutes,
  deep_sleep_minutes = EXCLUDED.deep_sleep_minutes,
  light_sleep_minutes = EXCLUDED.light_sleep_minutes,
  rem_sleep_minutes = EXCLUDED.rem_sleep_minutes,
  awake_minutes = EXCLUDED.awake_minutes,
  sleep_score = EXCLUDED.sleep_score,
  bedtime = EXCLUDED.bedtime,
  wake_time = EXCLUDED.wake_time,
  source = EXCLUDED.source;
"""

def seconds_to_minutes(value):
    if value is None:
        return 0
    return int(value // 60)



def normalize_sleep_record(raw: dict, user_id: str):
    """
    Convert a raw Garmin sleep record into a sleep_summary-shaped dict.
    """
    deep_min = seconds_to_minutes(raw.get("deepSleepSeconds"))
    light_min = seconds_to_minutes(raw.get("lightSleepSeconds"))
    rem_min = seconds_to_minutes(raw.get("remSleepSeconds"))
    awake_min = seconds_to_minutes(raw.get("awakeSleepSeconds"))

    total_sleep_min = deep_min + light_min + rem_min
    
    if total_sleep_min == 0:
        return None  

    return {
        "user_id": user_id,
        "date": raw.get("calendarDate"),

        "total_sleep_minutes": total_sleep_min,
        "deep_sleep_minutes": deep_min,
        "light_sleep_minutes": light_min,
        "rem_sleep_minutes": rem_min,
        "awake_minutes": awake_min,

        "sleep_score": (
            raw.get("sleepScores", {}).get("overallScore")
        ),

        "bedtime": raw.get("sleepStartTimestampGMT"),
        "wake_time": raw.get("sleepEndTimestampGMT"),

        "source": "garmin",
    }

def load_sleep_file(path: Path):
    with open(path, "r") as f:
        return json.load(f)

from scripts.ingest.db import get_conn

USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"

def main():
    # --- load file (your existing logic) ---
    repo_root = Path(__file__).resolve().parents[2]

    sleep_dir = (
        repo_root
        / "data"
        / "raw"
        / "garmin_export_2025-12-31"
        / "DI_CONNECT"
        / "DI-Connect-Wellness"
    )

    matches = list(sleep_dir.glob("*sleepData.json"))
    if not matches:
        raise FileNotFoundError(f"No sleepData.json found in {sleep_dir}")
    
    records = []

    for path in matches:
        file_records = load_sleep_file(path)
        print(f"Loaded {len(file_records)} records from {path.name}")
        records.extend(file_records)

    rows = []
    for r in records:
        if "sleepStartTimestampGMT" not in r:
            continue

        rows.append(
            normalize_sleep_record(
                raw=r,
                user_id=USER_ID
            )
        )

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(SLEEP_UPSERT_SQL, rows)
        conn.commit()

    print(f"Upserted {len(rows)} sleep rows")


if __name__ == "__main__":
    main()
