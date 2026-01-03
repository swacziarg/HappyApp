def insert_prediction(conn, prediction):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO predictions (
                user_id,
                date,
                predicted_mood,
                confidence,
                explanation,
                model_version
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, date) DO UPDATE SET
                predicted_mood = EXCLUDED.predicted_mood,
                confidence = EXCLUDED.confidence,
                explanation = EXCLUDED.explanation,
                model_version = EXCLUDED.model_version,
                created_at = now();
            """,
            (
                prediction["user_id"],
                prediction["date"],
                prediction["predicted_mood"],
                prediction["confidence"],
                prediction["explanation"],
                prediction["model_version"],
            )
        )
