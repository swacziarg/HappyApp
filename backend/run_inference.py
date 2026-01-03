from db.connection import get_db_connection
from db.fetch_features import fetch_unpredicted_days
from db.insert_prediction import insert_prediction
from inference.infer import infer_mood

USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"


def main():
    conn = get_db_connection()

    try:
        rows = fetch_unpredicted_days(conn, USER_ID)

        for row in rows:
            result = infer_mood(row)

            prediction = {
                "user_id": row["user_id"],
                "date": row["date"],
                "predicted_mood": result["predicted_mood"],
                "confidence": result["confidence"],
                "explanation": result["explanation"],
                "model_version": result["model_version"],
            }

            insert_prediction(conn, prediction)
            print(f"✔ Predicted {row['date']} → mood {result['predicted_mood']}")

        conn.commit()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
