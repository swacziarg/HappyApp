from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
from pathlib import Path
import tempfile
import zipfile
import shutil
import hashlib

from backend.auth.supabase import get_current_user
from backend.db.connection import get_db_connection
from backend.garmin.orchestrator import process_garmin_upload

router = APIRouter(prefix="/garmin", tags=["garmin"])

# ─────────────────────────────────────────────
# Helpers: file handling
# ─────────────────────────────────────────────

def extract_uploads(files: List[UploadFile], tmpdir: Path) -> list[Path]:
    extracted: list[Path] = []

    for f in files:
        if not f.filename:
            continue

        if f.filename.endswith(".zip"):
            zip_path = tmpdir / f.filename
            with open(zip_path, "wb") as out:
                shutil.copyfileobj(f.file, out)

            with zipfile.ZipFile(zip_path) as z:
                z.extractall(tmpdir)

        elif f.filename.endswith(".json"):
            path = tmpdir / f.filename
            with open(path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            extracted.append(path)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {f.filename}",
            )

    # Collect all JSON files (zip or direct)
    extracted.extend(tmpdir.rglob("*.json"))
    return extracted


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ─────────────────────────────────────────────
# Helpers: upload tracking / idempotency
# ─────────────────────────────────────────────

def record_upload(user_id: str, filename: str, file_hash: str) -> bool:
    """
    Insert upload record.
    Returns True if inserted (new file), False if already exists.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO garmin_uploads (
                    user_id,
                    filename,
                    file_hash,
                    status
                )
                VALUES (%s, %s, %s, 'processing')
                ON CONFLICT (user_id, file_hash)
                DO NOTHING;
                """,
                (user_id, filename, file_hash),
            )
            inserted = cur.rowcount == 1
        conn.commit()
        return inserted
    finally:
        conn.close()


def mark_upload_success(file_hash: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE garmin_uploads
                SET status = 'success', error_message = NULL
                WHERE file_hash = %s;
                """,
                (file_hash,),
            )
        conn.commit()
    finally:
        conn.close()


def mark_upload_failed(file_hash: str, error: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE garmin_uploads
                SET status = 'failed', error_message = %s
                WHERE file_hash = %s;
                """,
                (error, file_hash),
            )
        conn.commit()
    finally:
        conn.close()

# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post("/upload")
def upload_garmin_files(
    files: List[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    user_id = user["sub"]

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    processed_files: list[Path] = []
    file_hashes: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # 1️⃣ Extract uploads
        all_json = extract_uploads(files, tmpdir)
        if not all_json:
            raise HTTPException(
                status_code=400,
                detail="No JSON files found in upload",
            )

        # 2️⃣ Idempotency check + tracking
        for path in all_json:
            fh = hash_file(path)
            is_new = record_upload(user_id, path.name, fh)
            if is_new:
                processed_files.append(path)
                file_hashes.append(fh)

        if not processed_files:
            return {
                "days_ingested": 0,
                "days_predicted": 0,
                "message": "All files were already processed",
            }

        try:
            # 3️⃣ Orchestrate full pipeline
            result = process_garmin_upload(
                user_id=user_id,
                files=processed_files,
            )

            # 4️⃣ Mark uploads successful
            for fh in file_hashes:
                mark_upload_success(fh)

        except Exception as e:
            for fh in file_hashes:
                mark_upload_failed(fh, str(e))
            raise

    return result
