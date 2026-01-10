import json
import gzip
from pathlib import Path
from scripts.ingest.db import get_conn


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


# ─────────────────────────────────────────────
# Robust Garmin JSON loader
# ─────────────────────────────────────────────

def load_garmin_json(path: Path) -> list[dict]:
    def valid(data):
        return isinstance(data, list) and len(data) > 0

    # gzip
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
            if valid(data):
                return data
    except Exception:
        pass

    # utf-8 with BOM
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            if valid(data):
                return data
    except Exception:
        pass

    # binary fallback
    try:
        raw = path.read_bytes()
        if not raw.strip():
            print(f"⚠️  Skipping empty file: {path.name}")
            return []

        text = raw.decode("utf-8", errors="ignore").strip()
        if not text:
            print(f"⚠️  Skipping undecodable file: {path.name}")
            return []

        data = json.loads(text)
        if valid(data):
            return data

    except Exception as e:
        print(f"⚠️  Skipping invalid JSON {path.name}: {e}")
        return []

    print(f"⚠️  Skipping unsupported file: {path.name}")
    return []


# ─────────────────────────────────────────────
# Normalizer
# ─────────────────────────────────────────────

def normalize_health_status_record(raw: dict, user_id: str):
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

    date = raw.get("calendarDate")
    if not date:
        return None

    return {
        "user_id": user_id,
        "date": date,
        "resting_hr": resting_hr,
        "respiration_rate": respiration_rate,
        "hrv_rmssd": hrv_rmssd,
        "source": "garmin",
    }


# ─────────────────────────────────────────────
# Ingest
# ─────────────────────────────────────────────

def ingest_health_status(files: list[Path], user_id: str):
    records = []

    for path in files:
        file_records = load_garmin_json(path)
        print(f"Loaded {len(file_records)} records from {path.name}")
        records.extend(file_records)

    rows = []
    for r in records:
        row = normalize_health_status_record(r, user_id)
        if row:
            rows.append(row)

    if not rows:
        print("No daily_physiology rows to ingest")
        return

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(HEALTH_STATUS_UPSERT_SQL, rows)
        conn.commit()

    print(f"Upserted {len(rows)} daily_physiology rows")


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

    ingest_health_status(files, USER_ID)


if __name__ == "__main__":
    main()
