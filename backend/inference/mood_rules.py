
def clamp(value, min_value=1.0, max_value=5.0):
    return max(min_value, min(max_value, value))


def sleep_contribution(row):
    delta = 0.0

    debt = row.get("sleep_debt_minutes")
    if debt is not None:
        if debt <= 0:
            delta += 0.3
        elif debt <= 30:
            pass
        elif debt <= 90:
            delta -= 0.4
        else:
            delta -= 0.8

    pct = row.get("sleep_vs_baseline_pct")
    if pct is not None:
        if pct >= 10:
            delta += 0.3
        elif pct <= -10:
            delta -= 0.4

    return delta


def cardio_contribution(row):
    delta = 0.0

    hrv = row.get("hrv_rmssd_zscore")
    if hrv is not None:
        if hrv >= 1.0:
            delta += 0.6
        elif hrv >= 0.3:
            delta += 0.3
        elif hrv <= -1.0:
            delta -= 0.7
        elif hrv <= -0.3:
            delta -= 0.4

    rhr = row.get("resting_hr_delta")
    if rhr is not None:
        if rhr <= -3:
            delta += 0.3
        elif rhr >= 3:
            delta -= 0.4

    return delta


def stress_contribution(row):
    delta = 0.0

    stress = row.get("stress_percentile")
    if stress is not None:
        if stress <= 0.25:
            delta += 0.4
        elif stress <= 0.5:
            delta += 0.1
        elif stress <= 0.75:
            delta -= 0.3
        else:
            delta -= 0.6

    return delta


def activity_contribution(row):
    delta = 0.0

    steps = row.get("steps_vs_baseline_pct")
    if steps is not None:
        if steps >= 20:
            delta += 0.3
        elif steps <= -20:
            delta -= 0.2

    active = row.get("active_minutes_delta")
    if active is not None:
        if active >= 20:
            delta += 0.2
        elif active <= -20:
            delta -= 0.2

    return delta
