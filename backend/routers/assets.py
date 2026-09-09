from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
from schemas import AssetCreate, AssetOut
from auth_utils import get_current_user
from analysis_pipeline import run_full_analysis

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("")
def list_assets(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assets = db.query(models.Asset).all()
    result = []
    for a in assets:
        latest_pred = (
            db.query(models.Prediction)
            .filter(models.Prediction.asset_id == a.id)
            .order_by(models.Prediction.created_at.desc())
            .first()
        )
        latest_iw = (
            db.query(models.InterventionWindow)
            .filter(models.InterventionWindow.asset_id == a.id)
            .order_by(models.InterventionWindow.created_at.desc())
            .first()
        )
        result.append({
            "id": a.id,
            "machine_id": a.machine_id,
            "name": a.name,
            "type": a.type,
            "location": a.location,
            "status": a.status,
            "health_score": latest_pred.health_score if latest_pred else None,
            "risk_level": latest_pred.risk_level if latest_pred else None,
            "critical_time_hours": latest_pred.critical_time_hours if latest_pred else None,
            "intervention_start": latest_iw.window_start_hours if latest_iw else None,
            "intervention_end": latest_iw.window_end_hours if latest_iw else None,
        })
    return result


@router.post("", response_model=AssetOut)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    existing = db.query(models.Asset).filter(models.Asset.machine_id == payload.machine_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Machine ID already exists")
    asset = models.Asset(**payload.dict())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    db.add(models.AssetThreshold(asset_id=asset.id))
    db.add(models.CostModel(asset_id=asset.id))
    db.commit()
    return asset


@router.get("/{machine_id}")
def get_asset(machine_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {
        "id": asset.id,
        "machine_id": asset.machine_id,
        "name": asset.name,
        "type": asset.type,
        "location": asset.location,
        "installation_date": asset.installation_date,
        "operating_hours": asset.operating_hours,
        "status": asset.status,
    }


@router.get("/{machine_id}/readings")
def get_readings(machine_id: str, limit: int = 200, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    readings = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.asset_id == asset.id)
        .order_by(models.SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    readings.reverse()
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "vibration": r.vibration,
            "current": r.current_amp,
            "load": r.load_pct,
            "is_anomaly": bool(r.is_anomaly),
        }
        for r in readings
    ]


@router.get("/{machine_id}/analysis")
def get_asset_analysis(machine_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    result = run_full_analysis(db, asset)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    failures = (
        db.query(models.FailureRecord)
        .filter(models.FailureRecord.asset_id == asset.id)
        .order_by(models.FailureRecord.failure_date.desc())
        .all()
    )
    maintenance = (
        db.query(models.MaintenanceRecord)
        .filter(models.MaintenanceRecord.asset_id == asset.id)
        .order_by(models.MaintenanceRecord.created_at.desc())
        .all()
    )

    result["asset_info"] = {
        "machine_id": asset.machine_id,
        "name": asset.name,
        "type": asset.type,
        "location": asset.location,
        "installation_date": str(asset.installation_date) if asset.installation_date else None,
        "operating_hours": asset.operating_hours,
    }
    result["failure_history"] = [
        {
            "date": f.failure_date.isoformat() if f.failure_date else None,
            "description": f.description,
            "repair_cost": f.repair_cost,
            "production_loss": f.production_loss,
        }
        for f in failures
    ]
    result["maintenance_history"] = [
        {
            "type": m.maintenance_type,
            "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
            "completed_at": m.completed_at.isoformat() if m.completed_at else None,
            "cost": m.cost,
            "downtime_hours": m.downtime_hours,
            "status": m.status,
            "notes": m.notes,
        }
        for m in maintenance
    ]
    return result
