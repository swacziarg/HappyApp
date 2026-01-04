from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class TodayResponse(BaseModel):
    date: date
    predicted_mood: Optional[float]
    confidence: Optional[str]
    explanation: List[str]
    model_version: Optional[str]
    status: str
    reason: Optional[str] = None


class HistoryDay(BaseModel):
    date: date
    predicted_mood: Optional[float]
    confidence: Optional[str]
    explanation: List[str]
    status: str


class HistoryResponse(BaseModel):
    start: date
    end: date
    days: List[HistoryDay]

class MoodCreate(BaseModel):
    date: date
    mood: int = Field(ge=1, le=5)
    note: Optional[str] = None


class MoodResponse(BaseModel):
    date: date
    mood: int
    note: Optional[str]
    created_at: datetime



class MoodDay(BaseModel):
    date: date
    mood: Optional[int]
    note: Optional[str]
    status: str
    created_at: Optional[datetime]



class MoodHistoryResponse(BaseModel):
    start: date
    end: date
    days: List[MoodDay]