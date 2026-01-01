import os
import psycopg
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load backend/.env
repo_root = Path(__file__).resolve().parents[2]
env_path = repo_root / "backend" / ".env"
load_dotenv(env_path)


@contextmanager
def get_conn():
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()