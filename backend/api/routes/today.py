from fastapi import APIRouter, Depends
from datetime import date

from backend.db.connection import get_db_connection
from backend.api.schemas import TodayResponse
from backend.auth.supabase import get_current_user

router = APIRouter()

@router.get("/today", response_model=TodayResponse)
def get_today(user=Depends(get_current_user)):
    today = date.today()
    user_id = user["sub"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT predicted_mood, confidence, explanation, model_version
        FROM predictions
        WHERE user_id = %s
          AND date = %s
        LIMIT 1
        """,
        (user_id, today)
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return TodayResponse(
            date=today,
            predicted_mood=None,
            confidence=None,
            explanation=[],
            model_version=None,
            status="not_computed",
            reason="No prediction exists for this date",
        )

    predicted_mood, confidence, explanation, model_version = row

    return TodayResponse(
        date=today,
        predicted_mood=predicted_mood,
        confidence=confidence,
        explanation=explanation,
        model_version=model_version,
        status="available",
    )
