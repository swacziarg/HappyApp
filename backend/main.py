from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import today, history, mood

app = FastAPI(title="Garmin → Mood API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://swacziarg.github.io", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(today.router)
app.include_router(history.router)
app.include_router(mood.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
