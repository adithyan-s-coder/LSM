from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("")
def list_predictions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assets = db.query(models.Asset).all()
    out = []
    for a in assets:
        latest_pred = (
            db.query(models.Prediction)
            .filter(models.Prediction.asset_id == a.id)
            .order_by(models.Prediction.created_at.desc())
            .first()
        )
        if not latest_pred:
            continue
        latest_iw = (
            db.query(models.InterventionWindow)
            .filter(models.InterventionWindow.asset_id == a.id)
            .order_by(models.InterventionWindow.created_at.desc())
            .first()
        )
        out.append({
            "machine_id": a.machine_id,
            "name": a.name,
            "health_score": latest_pred.health_score,
            "risk_level": latest_pred.risk_level,
            "critical_time_hours": latest_pred.critical_time_hours,
            "intervention_start": latest_iw.window_start_hours if latest_iw else None,
            "intervention_end": latest_iw.window_end_hours if latest_iw else None,
            "confidence": latest_pred.confidence,
            "updated_at": latest_pred.created_at.isoformat(),
        })
    return out


@router.get("/{machine_id}/history")
def prediction_history(machine_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    preds = (
        db.query(models.Prediction)
        .filter(models.Prediction.asset_id == asset.id)
        .order_by(models.Prediction.created_at.asc())
        .all()
    )
    return [
        {
            "health_score": p.health_score,
            "risk_level": p.risk_level,
            "critical_time_hours": p.critical_time_hours,
            "confidence": p.confidence,
            "created_at": p.created_at.isoformat(),
        }
        for p in preds
    ]
