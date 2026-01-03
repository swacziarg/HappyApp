import json
from pathlib import Path
from scripts.ingest.db import get_conn

USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"

# ─────────────────────────────────────────────
# SQL
# ─────────────────────────────────────────────

ACTIVITY_UPSERT_SQL = """
INSERT INTO daily_activity (
  user_id,
  date,
  steps,
  active_minutes,
  calories_burned,
  distance_meters,
  source
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(steps)s,
  %(active_minutes)s,
  %(calories_burned)s,
  %(distance_meters)s,
  %(source)s
)
ON CONFLICT (user_id, date)
DO UPDATE SET
  steps = COALESCE(EXCLUDED.steps, daily_activity.steps),
  active_minutes = COALESCE(EXCLUDED.active_minutes, daily_activity.active_minutes),
  calories_burned = COALESCE(EXCLUDED.calories_burned, daily_activity.calories_burned),
  distance_meters = COALESCE(EXCLUDED.distance_meters, daily_activity.distance_meters),
  source = EXCLUDED.source;
"""

STRESS_INSERT_SQL = """
INSERT INTO daily_stress (
  user_id,
  date,
  stress_type,
  avg_stress,
  max_stress,
  stress_duration,
  rest_duration,
  activity_duration,
  total_duration
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(stress_type)s,
  %(avg_stress)s,
  %(max_stress)s,
  %(stress_duration)s,
  %(rest_duration)s,
  %(activity_duration)s,
  %(total_duration)s
)
ON CONFLICT DO NOTHING;
"""

BODY_BATTERY_INSERT_SQL = """
INSERT INTO daily_body_battery (
  user_id,
  date,
  stat_type,
  value,
  timestamp
)
VALUES (
  %(user_id)s,
  %(date)s,
  %(stat_type)s,
  %(value)s,
  %(timestamp)s
)
ON CONFLICT DO NOTHING;
"""

# ─────────────────────────────────────────────
# NORMALIZERS
# ─────────────────────────────────────────────

def normalize_activity(raw):
    active_minutes = None
    if raw.get("moderateIntensityMinutes") is not None or raw.get("vigorousIntensityMinutes") is not None:
        active_minutes = (raw.get("moderateIntensityMinutes") or 0) + (raw.get("vigorousIntensityMinutes") or 0)

    return {
        "user_id": USER_ID,
        "date": raw.get("calendarDate"),
        "steps": raw.get("totalSteps"),
        "calories_burned": raw.get("totalKilocalories"),
        "distance_meters": raw.get("totalDistanceMeters"),
        "active_minutes": active_minutes,
        "source": "garmin",
    }


def normalize_stress(raw):
    stress = raw.get("allDayStress")
    if not stress:
        return []

    rows = []
    for agg in stress.get("aggregatorList", []):
        rows.append({
            "user_id": USER_ID,
            "date": raw["calendarDate"],
            "stress_type": agg.get("type"),
            "avg_stress": agg.get("averageStressLevel"),
            "max_stress": agg.get("maxStressLevel"),
            "stress_duration": agg.get("stressDuration"),
            "rest_duration": agg.get("restDuration"),
            "activity_duration": agg.get("activityDuration"),
            "total_duration": agg.get("totalDuration"),
        })
    return rows


def normalize_body_battery(raw):
    bb = raw.get("bodyBattery")
    if not bb:
        return []

    rows = []
    for stat in bb.get("bodyBatteryStatList", []):
        rows.append({
            "user_id": USER_ID,
            "date": raw["calendarDate"],
            "stat_type": stat.get("bodyBatteryStatType"),
            "value": stat.get("statsValue"),
            "timestamp": stat.get("statTimestamp"),
        })
    return rows


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

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

    files = sorted(uds_dir.glob("UDSFile_*.json"))
    if not files:
        raise FileNotFoundError("No UDS files found")

    activity_rows = []
    stress_rows = []
    body_battery_rows = []

    for path in files:
        records = json.load(open(path))
        print(f"Loaded {len(records)} records from {path.name}")

        for r in records:
            activity_rows.append(normalize_activity(r))
            stress_rows.extend(normalize_stress(r))
            body_battery_rows.extend(normalize_body_battery(r))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(ACTIVITY_UPSERT_SQL, activity_rows)
            cur.executemany(STRESS_INSERT_SQL, stress_rows)
            cur.executemany(BODY_BATTERY_INSERT_SQL, body_battery_rows)
        conn.commit()

    print(f"Upserted {len(activity_rows)} daily_activity rows")
    print(f"Inserted {len(stress_rows)} daily_stress rows")
    print(f"Inserted {len(body_battery_rows)} daily_body_battery rows")


if __name__ == "__main__":
    main()
