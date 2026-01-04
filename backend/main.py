from fastapi import FastAPI

from backend.api.routes import today, history, mood

app = FastAPI(title="Garmin → Mood API")

app.include_router(today.router)
app.include_router(history.router)
app.include_router(mood.router)


@app.get("/")
def read_root():
    return {"status": "ok"}
