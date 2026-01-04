from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta

from backend.db.connection import get_db_connection
from backend.api.schemas import (
    MoodCreate,
    MoodResponse,
    MoodHistoryResponse,
    MoodDay,
)


router = APIRouter()

# TEMP: single-user placeholder until auth exists
DEFAULT_USER_ID = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"


@router.post("/mood", response_model=MoodResponse)
def upsert_mood(mood: MoodCreate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO mood_labels (
                user_id,
                date,
                mood,
                note,
                created_at
            )
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                mood = EXCLUDED.mood,
                note = EXCLUDED.note
            RETURNING
                date,
                mood,
                note,
                created_at
            """,
            (
                DEFAULT_USER_ID,
                mood.date,
                mood.mood,
                mood.note
            )
        )

        row = cur.fetchone()
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save mood label: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()

    return {
        "date": row[0],
        "mood": row[1],
        "note": row[2],
        "created_at": row[3]
    }


@router.get("/mood", response_model=MoodHistoryResponse)
def get_mood_history(
    start: date = Query(...),
    end: date = Query(...)
):
    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start date must be before end date"
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                date,
                mood,
                note,
                created_at
            FROM mood_labels
            WHERE user_id = %s
              AND date BETWEEN %s AND %s
            ORDER BY date
            """,
            (
                DEFAULT_USER_ID,
                start,
                end,
            )
        )

        rows = cur.fetchall()
        rows_by_date = {
            row[0]: row[1:] for row in rows
        }

    finally:
        cur.close()
        conn.close()

    days = []
    current = start

    while current <= end:
        if current in rows_by_date:
            mood, note, created_at = rows_by_date[current]
            days.append(
                MoodDay(
                    date=current,
                    mood=mood,
                    note=note,
                    status="available",
                    created_at=created_at
                )
            )
        else:
            days.append(
                MoodDay(
                    date=current,
                    mood=None,
                    note=None,
                    status="missing",
                    created_at=None
                )
            )

        current += timedelta(days=1)

    return MoodHistoryResponse(
        start=start,
        end=end,
        days=days,
    )
