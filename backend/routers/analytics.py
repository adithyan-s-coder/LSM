from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def get_analytics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assets = db.query(models.Asset).all()

    health_distribution = []
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    health_over_time = {}

    for a in assets:
        latest_pred = (
            db.query(models.Prediction)
            .filter(models.Prediction.asset_id == a.id)
            .order_by(models.Prediction.created_at.desc())
            .first()
        )
        if latest_pred:
            health_distribution.append({"machine_id": a.machine_id, "health_score": latest_pred.health_score})
            if latest_pred.risk_level in risk_distribution:
                risk_distribution[latest_pred.risk_level] += 1

        preds = (
            db.query(models.Prediction)
            .filter(models.Prediction.asset_id == a.id)
            .order_by(models.Prediction.created_at.asc())
            .all()
        )
        health_over_time[a.machine_id] = [
            {"created_at": p.created_at.isoformat(), "health_score": p.health_score} for p in preds
        ]

    maintenance_cost_total = db.query(func.coalesce(func.sum(models.MaintenanceRecord.cost), 0)).scalar()
    downtime_total = db.query(func.coalesce(func.sum(models.MaintenanceRecord.downtime_hours), 0)).scalar()
    anomaly_count = db.query(func.coalesce(func.sum(models.SensorReading.is_anomaly), 0)).scalar()
    failure_count = db.query(func.count(models.FailureRecord.id)).scalar()

    return {
        "health_distribution": health_distribution,
        "risk_distribution": risk_distribution,
        "health_over_time": health_over_time,
        "maintenance_cost_total": float(maintenance_cost_total or 0),
        "downtime_total_hours": float(downtime_total or 0),
        "anomaly_count": int(anomaly_count or 0),
        "failure_count": int(failure_count or 0),
    }
