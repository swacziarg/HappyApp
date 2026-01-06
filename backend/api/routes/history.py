from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date, timedelta

from backend.db.connection import get_db_connection
from backend.api.schemas import HistoryResponse, HistoryDay
from backend.auth.supabase import get_current_user

router = APIRouter()

@router.get("/history", response_model=HistoryResponse)
def get_history(
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
        SELECT date, predicted_mood::float, confidence, explanation
        FROM predictions
        WHERE user_id = %s
          AND date BETWEEN %s AND %s
        ORDER BY date
        """,
        (user_id, start, end),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    rows_by_date = {
        row[0]: (row[1], row[2], row[3]) for row in rows
    }

    days = []
    current = start

    while current <= end:
        if current in rows_by_date:
            predicted_mood, confidence, explanation = rows_by_date[current]
            days.append(
                HistoryDay(
                    date=current,
                    predicted_mood=predicted_mood,
                    confidence=confidence,
                    explanation=explanation,
                    status="available",
                )
            )
        else:
            days.append(
                HistoryDay(
                    date=current,
                    predicted_mood=None,
                    confidence=None,
                    explanation=[],
                    status="missing",
                )
            )

        current += timedelta(days=1)

    return HistoryResponse(
        start=start,
        end=end,
        days=days,
    )
