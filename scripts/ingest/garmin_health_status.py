from scripts.ingest.db import get_conn
from pathlib import Path
import json


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


def normalize_health_status_record(raw: dict, user_id: str):
    metrics = raw.get("metrics", [])

    resting_hr = None
    respiration_rate = None
    hrv_rmssd = None

    for m in metrics:
        metric_type = m.get("type")
        value = m.get("value")

        if value is None:
            continue

        if metric_type == "HR":
            resting_hr = int(value)

        elif metric_type == "RESPIRATION":
            respiration_rate = float(value)

        elif metric_type == "HRV":
            # Garmin healthStatus HRV is RMSSD-style nightly HRV
            hrv_rmssd = float(value)

    return {
        "user_id": user_id,
        "date": raw.get("calendarDate"),

        "resting_hr": resting_hr,
        "respiration_rate": respiration_rate,
        "hrv_rmssd": hrv_rmssd,

        "source": "garmin",
    }


USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"


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

    matches = list(wellness_dir.glob("*healthStatusData.json"))
    if not matches:
        raise FileNotFoundError("No healthStatusData.json found")

    records = json.load(open(matches[0]))
    print(f"Loaded {len(records)} health status records")

    rows = []
    for r in records:
        normalized = normalize_health_status_record(
            raw=r,
            user_id=USER_ID
        )
        rows.append(normalized)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(HEALTH_STATUS_UPSERT_SQL, rows)
        conn.commit()

    print(f"Upserted {len(rows)} daily physiology rows")


if __name__ == "__main__":
    main()
