from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
from pathlib import Path
import tempfile
import zipfile
import shutil

from backend.auth.supabase import get_current_user

from scripts.ingest.garmin_sleep import ingest_sleep
from scripts.ingest.garmin_health_status import ingest_health_status
from scripts.ingest.garmin_uds import ingest_uds

from scripts.compute_daily_features import compute_daily_features_for_user
from backend.run_inference import run_inference_for_user

router = APIRouter(prefix="/garmin", tags=["garmin"])

def extract_uploads(files: List[UploadFile], tmpdir: Path) -> list[Path]:
    extracted: list[Path] = []

    for f in files:
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

    # collect all json files (zip or direct)
    extracted.extend(tmpdir.rglob("*.json"))
    return extracted

def partition_garmin_files(files: list[Path]):
    sleep = []
    health = []
    uds = []

    for path in files:
        name = path.name

        if name.endswith("sleepData.json"):
            sleep.append(path)
        elif name.endswith("healthStatusData.json"):
            health.append(path)
        elif name.startswith("UDSFile_"):
            uds.append(path)

    return sleep, health, uds

@router.post("/upload")
def upload_garmin_files(
    files: List[UploadFile] = File(...),
):
    user_id = "b1101f5b-a68d-4cb9-bf48-bfc4697a761a"


    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # 1️⃣ Extract uploads
        all_json = extract_uploads(files, tmpdir)

        if not all_json:
            raise HTTPException(
                status_code=400,
                detail="No JSON files found in upload",
            )

        # 2️⃣ Partition files
        sleep_files, health_files, uds_files = partition_garmin_files(all_json)

        # 3️⃣ Ingest
        if sleep_files:
            ingest_sleep(sleep_files, user_id)

        if health_files:
            ingest_health_status(health_files, user_id)

        if uds_files:
            ingest_uds(uds_files, user_id)

        # 4️⃣ Compute features
        compute_daily_features_for_user(user_id)

        # 5️⃣ Run inference
        predicted = run_inference_for_user(user_id)

    return {
        "days_ingested": len(set(p.stem for p in all_json)),
        "days_predicted": predicted,
    }
