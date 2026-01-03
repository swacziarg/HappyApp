FEATURE_KEYS = [
    "sleep_debt_minutes",
    "sleep_vs_baseline_pct",
    "hrv_rmssd_zscore",
    "resting_hr_delta",
    "stress_percentile",
    "steps_vs_baseline_pct",
    "active_minutes_delta",
]


def compute_confidence(row):
    present = sum(1 for k in FEATURE_KEYS if row.get(k) is not None)

    if present >= 5:
        return "high"
    if present >= 3:
        return "medium"
    return "low"
