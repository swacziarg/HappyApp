import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv("backend/.env")

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def main():
    conn = get_conn()

    query = """
    SELECT
      p.date,
      p.predicted_mood,
      m.mood AS actual_mood
    FROM predictions p
    JOIN mood_labels m
      ON p.user_id = m.user_id
     AND p.date = m.date
    ORDER BY p.date;
    """

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("No overlapping prediction + mood label days.")
        return

    df["error"] = df["predicted_mood"] - df["actual_mood"]
    df["abs_error"] = df["error"].abs()

    print("\n=== BASIC STATS ===")
    print(df.describe())

    print("\n=== ERROR DISTRIBUTION ===")
    print(df["error"].value_counts().sort_index())

    print("\n=== AGREEMENT METRICS ===")
    exact = (df["abs_error"] == 0).mean()
    within_1 = (df["abs_error"] <= 1).mean()

    print(f"Exact match rate: {exact:.2%}")
    print(f"Within ±1 mood: {within_1:.2%}")

    print("\n=== CORRELATION ===")
    print("Pearson:", df["predicted_mood"].corr(df["actual_mood"]))
    print("Spearman:", df["predicted_mood"].corr(df["actual_mood"], method="spearman"))

    print("\n=== CONFUSION TABLE ===")
    print(pd.crosstab(df["actual_mood"], df["predicted_mood"]))

if __name__ == "__main__":
    main()
