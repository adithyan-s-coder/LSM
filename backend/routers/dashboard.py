from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from auth_utils import get_current_user
from analysis_pipeline import run_full_analysis

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assets = db.query(models.Asset).all()
    if not assets:
        return {"summary": {"total_assets": 0}, "priority_asset": None, "assets": []}

    asset_summaries = []
    priority_asset = None
    priority_score = -1

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
        risk_score = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
            latest_pred.risk_level if latest_pred else "LOW", 0
        )
        summary = {
            "machine_id": a.machine_id,
            "name": a.name,
            "health_score": latest_pred.health_score if latest_pred else None,
            "risk_level": latest_pred.risk_level if latest_pred else None,
            "critical_time_hours": latest_pred.critical_time_hours if latest_pred else None,
            "intervention_start": latest_iw.window_start_hours if latest_iw else None,
            "intervention_end": latest_iw.window_end_hours if latest_iw else None,
            "confidence": latest_pred.confidence if latest_pred else None,
            "status": a.status,
        }
        asset_summaries.append(summary)
        if risk_score > priority_score:
            priority_score = risk_score
            priority_asset = summary

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for s in asset_summaries:
        if s["risk_level"] in risk_counts:
            risk_counts[s["risk_level"]] += 1

    priority_full = None
    if priority_asset:
        asset_obj = db.query(models.Asset).filter(models.Asset.machine_id == priority_asset["machine_id"]).first()
        priority_full = run_full_analysis(db, asset_obj)

    return {
        "summary": {
            "total_assets": len(assets),
            "risk_counts": risk_counts,
        },
        "priority_asset": priority_full,
        "assets": asset_summaries,
    }
