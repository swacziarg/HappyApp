import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load backend/.env
repo_root = Path(__file__).resolve().parents[2]
env_path = repo_root / "backend" / ".env"
load_dotenv(env_path)


@contextmanager
def get_conn():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()