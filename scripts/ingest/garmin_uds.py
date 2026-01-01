import json
from pathlib import Path
from scripts.ingest.db import get_conn


UDS_UPSERT_SQL = """
INSERT INTO daily_physiology (
  user_id,
  date,
  steps,
  active_minutes,
  calories_burned,
  resting_hr,
  respiration_rate,
  source
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(steps)s,
  %(active_minutes)s,
  %(calories_burned)s,
  %(resting_hr)s,
  %(respiration_rate)s,
  %(source)s
)
ON CONFLICT (user_id, date)
DO UPDATE SET
  steps = COALESCE(EXCLUDED.steps, daily_physiology.steps),
  calories_burned = COALESCE(EXCLUDED.calories_burned, daily_physiology.calories_burned),
  active_minutes = COALESCE(EXCLUDED.active_minutes, daily_physiology.active_minutes),
  resting_hr = COALESCE(EXCLUDED.resting_hr, daily_physiology.resting_hr),
  respiration_rate = COALESCE(EXCLUDED.respiration_rate, daily_physiology.respiration_rate),
  source = EXCLUDED.source;

"""
def normalize_uds_record(raw: dict, user_id: str):
    """
    Normalize a Garmin UDS daily aggregate record into daily_physiology shape.
    """

    # Activity
    steps = raw.get("totalSteps")
    calories = raw.get("totalKilocalories")

    active_minutes = None
    if raw.get("moderateIntensityMinutes") is not None or raw.get("vigorousIntensityMinutes") is not None:
        active_minutes = (
            (raw.get("moderateIntensityMinutes") or 0)
            + (raw.get("vigorousIntensityMinutes") or 0)
        )

    # Backup physiology (only if present)
    resting_hr = raw.get("restingHeartRate")

    respiration_rate = None
    respiration = raw.get("respiration")
    if respiration:
        respiration_rate = respiration.get("avgWakingRespirationValue")

    return {
        "user_id": user_id,
        "date": raw.get("calendarDate"),

        "steps": steps,
        "calories_burned": calories,
        "active_minutes": active_minutes,

        # backup fills (will be COALESCE-safe)
        "resting_hr": resting_hr,
        "respiration_rate": respiration_rate,

        "source": "garmin",
    }


USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"

def main():
    repo_root = Path(__file__).resolve().parents[2]

    uds_dir = (
        repo_root
        / "data"
        / "raw"
        / "garmin_export_2025-12-31"
        / "DI_CONNECT"
        / "DI-Connect-Aggregator"
    )

    matches = sorted(uds_dir.glob("UDSFile_*.json"))
    if not matches:
        raise FileNotFoundError("No UDSFile found")

    all_records = []

    for path in matches:
        records = json.load(open(path))
        print(f"Loaded {len(records)} records from {path.name}")
        all_records.extend(records)

    print(f"Total UDS records: {len(all_records)}")

    rows = []
    for r in all_records:
        rows.append(
            normalize_uds_record(
                raw=r,
                user_id=USER_ID
            )
        )

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(UDS_UPSERT_SQL, rows)
        conn.commit()

    print(f"Upserted {len(rows)} daily physiology rows")



if __name__ == "__main__":
    main()
