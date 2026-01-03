import os
import logging
from datetime import timedelta

import psycopg2
import psycopg2.extras
import numpy as np
from dotenv import load_dotenv

# -------------------------------------------------
# Setup
# -------------------------------------------------

load_dotenv("backend/.env")

DB_URL = os.getenv("DATABASE_URL")

BASELINE_DAYS = 28
MIN_BASELINE_DAYS = 7
MIN_HRV_DAYS = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# -------------------------------------------------
# DB Helpers
# -------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL)


def fetch_users(cur):
    cur.execute("SELECT id FROM users;")
    return [row["id"] for row in cur.fetchall()]


def fetch_all_dates(cur, user_id):
    """
    Union of all dates where *any* raw data exists.
    """
    cur.execute(
        """
        SELECT DISTINCT date FROM (
            SELECT date FROM sleep_summary WHERE user_id = %s
            UNION
            SELECT date FROM daily_physiology WHERE user_id = %s
            UNION
            SELECT date FROM daily_activity WHERE user_id = %s
            UNION
            SELECT date FROM daily_stress WHERE user_id = %s
        ) d
        ORDER BY date;
        """,
        (user_id, user_id, user_id, user_id),
    )
    return [row["date"] for row in cur.fetchall()]


def fetch_baseline(cur, user_id, day):
    start_date = day - timedelta(days=BASELINE_DAYS)

    cur.execute(
        """
        SELECT
            ss.total_sleep_minutes,
            dp.hrv_rmssd,
            dp.resting_hr,
            da.steps,
            da.active_minutes,
            ds.avg_stress
        FROM sleep_summary ss
        LEFT JOIN daily_physiology dp
            ON ss.user_id = dp.user_id AND ss.date = dp.date
        LEFT JOIN daily_activity da
            ON ss.user_id = da.user_id AND ss.date = da.date
        LEFT JOIN daily_stress ds
            ON ss.user_id = ds.user_id
           AND ss.date = ds.date
           AND ds.stress_type = 'TOTAL'
        WHERE ss.user_id = %s
          AND ss.date >= %s
          AND ss.date < %s;
        """,
        (user_id, start_date, day),
    )

    return cur.fetchall()


def fetch_today(cur, user_id, day):
    cur.execute(
        """
        SELECT
            ss.total_sleep_minutes,
            dp.hrv_rmssd,
            dp.resting_hr,
            da.steps,
            da.active_minutes,
            ds.avg_stress
        FROM sleep_summary ss
        LEFT JOIN daily_physiology dp
            ON ss.user_id = dp.user_id AND ss.date = dp.date
        LEFT JOIN daily_activity da
            ON ss.user_id = da.user_id AND ss.date = da.date
        LEFT JOIN daily_stress ds
            ON ss.user_id = ds.user_id
           AND ss.date = ds.date
           AND ds.stress_type = 'TOTAL'
        WHERE ss.user_id = %s
          AND ss.date = %s;
        """,
        (user_id, day),
    )

    return cur.fetchone()


def upsert_features(cur, user_id, day, features):
    cur.execute(
        """
        INSERT INTO daily_features (
            user_id,
            date,
            sleep_debt_minutes,
            sleep_vs_baseline_pct,
            hrv_rmssd_zscore,
            resting_hr_delta,
            stress_percentile,
            steps_vs_baseline_pct,
            active_minutes_delta,
            baseline_window_days
        )
        VALUES (
            %(user_id)s,
            %(date)s,
            %(sleep_debt_minutes)s,
            %(sleep_vs_baseline_pct)s,
            %(hrv_rmssd_zscore)s,
            %(resting_hr_delta)s,
            %(stress_percentile)s,
            %(steps_vs_baseline_pct)s,
            %(active_minutes_delta)s,
            %(baseline_window_days)s
        )
        ON CONFLICT (user_id, date)
        DO UPDATE SET
            sleep_debt_minutes = EXCLUDED.sleep_debt_minutes,
            sleep_vs_baseline_pct = EXCLUDED.sleep_vs_baseline_pct,
            hrv_rmssd_zscore = EXCLUDED.hrv_rmssd_zscore,
            resting_hr_delta = EXCLUDED.resting_hr_delta,
            stress_percentile = EXCLUDED.stress_percentile,
            steps_vs_baseline_pct = EXCLUDED.steps_vs_baseline_pct,
            active_minutes_delta = EXCLUDED.active_minutes_delta,
            baseline_window_days = EXCLUDED.baseline_window_days,
            computed_at = NOW();
        """,
        {
            "user_id": user_id,
            "date": day,
            **features,
        },
    )

# -------------------------------------------------
# Stats Helpers
# -------------------------------------------------

def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def std(values):
    vals = [v for v in values if v is not None]
    return np.std(vals) if len(vals) >= 2 else None


def percentile_rank(value, values):
    vals = sorted(v for v in values if v is not None)
    if value is None or not vals:
        return None

    rank = np.searchsorted(vals, value, side="right")
    return rank / len(vals)


def to_python(value):
    """
    Convert numpy scalars to native Python types for psycopg2.
    """
    if value is None:
        return None
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value

# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for user_id in fetch_users(cur):
                logging.info(f"Processing user {user_id}")
                dates = fetch_all_dates(cur, user_id)

                for day in dates:
                    baseline = fetch_baseline(cur, user_id, day)
                    if len(baseline) < MIN_BASELINE_DAYS:
                        continue

                    today = fetch_today(cur, user_id, day)
                    if not today:
                        continue

                    sleep_vals = [r["total_sleep_minutes"] for r in baseline]
                    hrv_vals = [r["hrv_rmssd"] for r in baseline]
                    rhr_vals = [r["resting_hr"] for r in baseline]
                    stress_vals = [r["avg_stress"] for r in baseline]
                    steps_vals = [r["steps"] for r in baseline]
                    active_vals = [r["active_minutes"] for r in baseline]

                    features = {
                        "sleep_debt_minutes": None,
                        "sleep_vs_baseline_pct": None,
                        "hrv_rmssd_zscore": None,
                        "resting_hr_delta": None,
                        "stress_percentile": None,
                        "steps_vs_baseline_pct": None,
                        "active_minutes_delta": None,
                        "baseline_window_days": BASELINE_DAYS,
                    }

                    # Sleep
                    avg_sleep = mean(sleep_vals)
                    if avg_sleep and today["total_sleep_minutes"]:
                        features["sleep_debt_minutes"] = int(
                            avg_sleep - today["total_sleep_minutes"]
                        )
                        features["sleep_vs_baseline_pct"] = (
                            today["total_sleep_minutes"] / avg_sleep
                        ) - 1

                    # HRV
                    if len([v for v in hrv_vals if v is not None]) >= MIN_HRV_DAYS:
                        hrv_mean = mean(hrv_vals)
                        hrv_std = std(hrv_vals)
                        if hrv_std and today["hrv_rmssd"] is not None:
                            features["hrv_rmssd_zscore"] = (
                                today["hrv_rmssd"] - hrv_mean
                            ) / hrv_std

                    # Resting HR
                    avg_rhr = mean(rhr_vals)
                    if avg_rhr and today["resting_hr"] is not None:
                        features["resting_hr_delta"] = (
                            today["resting_hr"] - avg_rhr
                        )

                    # Stress
                    features["stress_percentile"] = percentile_rank(
                        today["avg_stress"], stress_vals
                    )

                    # Activity
                    avg_steps = mean(steps_vals)
                    if avg_steps and today["steps"] is not None:
                        features["steps_vs_baseline_pct"] = (
                            today["steps"] / avg_steps
                        ) - 1

                    avg_active = mean(active_vals)
                    if avg_active and today["active_minutes"] is not None:
                        features["active_minutes_delta"] = (
                            today["active_minutes"] - avg_active
                        )

                    features = {k: to_python(v) for k, v in features.items()}

                    upsert_features(cur, user_id, day, features)
                    logging.info(f"{day}: features computed")

        conn.commit()


if __name__ == "__main__":
    main()
