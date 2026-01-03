def fetch_unpredicted_days(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                user_id,
                date,
                sleep_debt_minutes,
                sleep_vs_baseline_pct,
                hrv_rmssd_zscore,
                resting_hr_delta,
                stress_percentile,
                steps_vs_baseline_pct,
                active_minutes_delta
            FROM daily_features df
            WHERE user_id = %s
              AND NOT EXISTS (
                SELECT 1 FROM predictions p
                WHERE p.user_id = df.user_id
                  AND p.date = df.date
              )
            ORDER BY date;
            """,
            (user_id,)
        )

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return [dict(zip(columns, row)) for row in rows]
