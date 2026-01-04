from fastapi import APIRouter
from datetime import date
from backend.db.connection import get_db_connection
from backend.api.schemas import TodayResponse

router = APIRouter()


@router.get("/today", response_model=TodayResponse)
def get_today():
    today = date.today()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT predicted_mood, confidence, explanation, model_version
        FROM predictions
        WHERE date = %s
        LIMIT 1
        """,
        (today,)
    )

    row = cur.fetchone()

    if row is None:
        return TodayResponse(
            date=today,
            predicted_mood=None,
            confidence=None,
            explanation=[],
            model_version=None,
            status="not_computed",
            reason="No prediction exists for this date"
        )

    predicted_mood, confidence, explanation, model_version = row

    return TodayResponse(
        date=today,
        predicted_mood=predicted_mood,
        confidence=confidence,
        explanation=explanation,
        model_version=model_version,
        status="available"
    )
