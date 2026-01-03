import json
from pathlib import Path
from scripts.ingest.db import get_conn

USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"

HEALTH_STATUS_UPSERT_SQL = """
INSERT INTO daily_physiology (
  user_id,
  date,
  resting_hr,
  respiration_rate,
  hrv_rmssd,
  source
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(resting_hr)s,
  %(respiration_rate)s,
  %(hrv_rmssd)s,
  %(source)s
)
ON CONFLICT (user_id, date)
DO UPDATE SET
  resting_hr = COALESCE(EXCLUDED.resting_hr, daily_physiology.resting_hr),
  respiration_rate = COALESCE(EXCLUDED.respiration_rate, daily_physiology.respiration_rate),
  hrv_rmssd = COALESCE(EXCLUDED.hrv_rmssd, daily_physiology.hrv_rmssd),
  source = EXCLUDED.source;
"""

def normalize_health_status_record(raw: dict):
    resting_hr = None
    respiration_rate = None
    hrv_rmssd = None

    for m in raw.get("metrics", []):
        value = m.get("value")
        if value is None:
            continue

        if m.get("type") == "HR":
            resting_hr = int(value)

        elif m.get("type") == "RESPIRATION":
            respiration_rate = float(value)

        elif m.get("type") == "HRV":
            hrv_rmssd = float(value)

    return {
        "user_id": USER_ID,
        "date": raw.get("calendarDate"),
        "resting_hr": resting_hr,
        "respiration_rate": respiration_rate,
        "hrv_rmssd": hrv_rmssd,
        "source": "garmin",
    }


def main():
    repo_root = Path(__file__).resolve().parents[2]
    wellness_dir = (
        repo_root
        / "data"
        / "raw"
        / "garmin_export_2025-12-31"
        / "DI_CONNECT"
        / "DI-Connect-Wellness"
    )

    files = list(wellness_dir.glob("*healthStatusData.json"))
    if not files:
        raise FileNotFoundError("No healthStatusData.json found")
    records = []

    for path in files:
        file_records = json.load(open(path))
        print(f"Loaded {len(file_records)} records from {path.name}")
        records.extend(file_records)

    rows = [normalize_health_status_record(r) for r in records]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(HEALTH_STATUS_UPSERT_SQL, rows)
        conn.commit()

    print(f"Upserted {len(rows)} daily_physiology rows")


if __name__ == "__main__":
    main()
