from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date, timedelta

from backend.db.connection import get_db_connection
from backend.api.schemas import (
    MoodCreate,
    MoodResponse,
    MoodHistoryResponse,
    MoodDay,
)
from backend.auth.supabase import get_current_user

router = APIRouter()

@router.post("/mood", response_model=MoodResponse)
def upsert_mood(
    mood: MoodCreate,
    user=Depends(get_current_user),
):
    user_id = user["sub"]

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
            RETURNING date, mood, note, created_at
            """,
            (user_id, mood.date, mood.mood, mood.note),
        )

        row = cur.fetchone()
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save mood label: {str(e)}",
        )

    finally:
        cur.close()
        conn.close()

    return MoodResponse(
        date=row[0],
        mood=row[1],
        note=row[2],
        created_at=row[3],
    )


@router.get("/mood", response_model=MoodHistoryResponse)
def get_mood_history(
    start: date = Query(...),
    end: date = Query(...),
    user=Depends(get_current_user),
):
    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start date must be before end date",
        )

    user_id = user["sub"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT date, mood, note, created_at
        FROM mood_labels
        WHERE user_id = %s
          AND date BETWEEN %s AND %s
        ORDER BY date
        """,
        (user_id, start, end),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    rows_by_date = {row[0]: row[1:] for row in rows}

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
                    created_at=created_at,
                )
            )
        else:
            days.append(
                MoodDay(
                    date=current,
                    mood=None,
                    note=None,
                    status="missing",
                    created_at=None,
                )
            )

        current += timedelta(days=1)

    return MoodHistoryResponse(
        start=start,
        end=end,
        days=days,
    )
