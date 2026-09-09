import io
import csv
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter(prefix="/api/data", tags=["data"])

REQUIRED_COLUMNS = {
    "timestamp", "machine_id", "temperature", "vibration", "current", "load", "operating_hours"
}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV appears to be empty")

    columns = set(c.strip() for c in reader.fieldnames)
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    inserted = 0
    skipped = 0
    errors = []
    touched_asset_ids = set()

    for i, row in enumerate(reader, start=2):  # start=2 to account for header line
        try:
            machine_id = row["machine_id"].strip()
            asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
            if not asset:
                errors.append(f"Row {i}: unknown machine_id '{machine_id}', skipped")
                skipped += 1
                continue

            ts_raw = row["timestamp"].strip()
            try:
                ts = datetime.fromisoformat(ts_raw)
            except ValueError:
                # try common alt format
                ts = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M")

            reading = models.SensorReading(
                asset_id=asset.id,
                timestamp=ts,
                temperature=float(row["temperature"]),
                vibration=float(row["vibration"]),
                current_amp=float(row["current"]),
                load_pct=float(row["load"]),
                operating_hours=float(row["operating_hours"]),
            )
            db.add(reading)
            touched_asset_ids.add(asset.id)
            inserted += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Row {i}: invalid data ({e}), skipped")
            skipped += 1

    db.commit()

    # Update operating_hours on touched assets to the latest reading
    for asset_id in touched_asset_ids:
        latest = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.asset_id == asset_id)
            .order_by(models.SensorReading.timestamp.desc())
            .first()
        )
        if latest:
            asset = db.query(models.Asset).get(asset_id)
            asset.operating_hours = latest.operating_hours
            db.add(asset)
    db.commit()

    return {
        "status": "processed",
        "rows_inserted": inserted,
        "rows_skipped": skipped,
        "assets_updated": len(touched_asset_ids),
        "errors": errors[:20],  # cap error list for readability
    }
