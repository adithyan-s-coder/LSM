import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import SimulationRequest
from auth_utils import get_current_user
from analysis_pipeline import run_full_analysis

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Per-hour drift applied for each scenario (base values, scaled by severity)
SCENARIOS = {
    "Healthy Machine": {"temp_drift": 0.0, "vib_drift": 0.0, "cur_drift": 0.0, "noise": 0.3},
    "Temporary Anomaly": {"temp_drift": 0.0, "vib_drift": 0.0, "cur_drift": 0.0, "noise": 0.3, "spike": True},
    "Gradual Deterioration": {"temp_drift": 0.35, "vib_drift": 0.15, "cur_drift": 0.05, "noise": 0.4},
    "Rapid Deterioration": {"temp_drift": 0.9, "vib_drift": 0.35, "cur_drift": 0.12, "noise": 0.5},
    "Near Failure": {"temp_drift": 1.4, "vib_drift": 0.55, "cur_drift": 0.2, "noise": 0.6},
}

SEVERITY_MULTIPLIER = {"low": 0.6, "medium": 1.0, "high": 1.6}


@router.post("/run")
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == payload.machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if payload.scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario. Choose from: {list(SCENARIOS.keys())}")

    # Capture "before" snapshot
    before = run_full_analysis(db, asset)

    cfg = SCENARIOS[payload.scenario]
    mult = SEVERITY_MULTIPLIER.get(payload.severity, 1.0)

    last = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.asset_id == asset.id)
        .order_by(models.SensorReading.timestamp.desc())
        .first()
    )
    start_temp = last.temperature if last else 60.0
    start_vib = last.vibration if last else 3.0
    start_cur = last.current_amp if last else 9.0
    start_load = last.load_pct if last else 60.0
    start_hours = last.operating_hours if last else asset.operating_hours or 1000.0
    start_ts = (last.timestamp if last else datetime.utcnow()) + timedelta(hours=1)

    new_readings = []
    for h in range(payload.duration_hours):
        temp = start_temp + cfg["temp_drift"] * mult * h + random.gauss(0, cfg["noise"])
        vib = start_vib + cfg["vib_drift"] * mult * h + random.gauss(0, cfg["noise"] * 0.3)
        cur = start_cur + cfg["cur_drift"] * mult * h + random.gauss(0, cfg["noise"] * 0.2)
        load = max(10, min(100, start_load + random.gauss(0, 3)))

        if cfg.get("spike") and h in (payload.duration_hours // 3, payload.duration_hours // 2):
            vib += 4.0
            temp += 6.0

        reading = models.SensorReading(
            asset_id=asset.id,
            timestamp=start_ts + timedelta(hours=h),
            temperature=round(max(20, temp), 2),
            vibration=round(max(0, vib), 2),
            current_amp=round(max(0, cur), 2),
            load_pct=round(load, 2),
            operating_hours=round(start_hours + h, 1),
        )
        db.add(reading)
        new_readings.append(reading)

    db.commit()

    asset.operating_hours = new_readings[-1].operating_hours
    db.add(asset)
    db.commit()

    # Re-run full pipeline to get the "after" state
    after = run_full_analysis(db, asset)

    return {
        "scenario": payload.scenario,
        "severity": payload.severity,
        "duration_hours": payload.duration_hours,
        "before": before,
        "after": after,
        "generated_readings": [
            {
                "timestamp": r.timestamp.isoformat(),
                "temperature": r.temperature,
                "vibration": r.vibration,
                "current": r.current_amp,
                "load": r.load_pct,
            }
            for r in new_readings
        ],
    }
