import os
import csv
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")

CSV_PATH = "data/raw/mood_labels.csv"


def get_conn():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(db_url)


def ingest_labels(csv_path):
    conn = get_conn()

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No rows found in CSV.")
        return

    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO mood_labels (
                        user_id,
                        date,
                        mood,
                        note
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, date)
                    DO UPDATE SET
                        mood = EXCLUDED.mood,
                        note = EXCLUDED.note,
                        created_at = now();
                    """,
                    (
                        row["user_id"],
                        row["date"],
                        int(row["mood"]),
                        row.get("note"),
                    ),
                )

        conn.commit()
        print(f"✔ Ingested {len(rows)} mood labels")

    finally:
        conn.close()


if __name__ == "__main__":
    ingest_labels(CSV_PATH)
