from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter(prefix="/api/intervention-windows", tags=["intervention-windows"])


@router.get("")
def list_intervention_windows(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assets = db.query(models.Asset).all()
    out = []
    for a in assets:
        iw = (
            db.query(models.InterventionWindow)
            .filter(models.InterventionWindow.asset_id == a.id)
            .order_by(models.InterventionWindow.created_at.desc())
            .first()
        )
        if not iw:
            continue
        out.append({
            "machine_id": a.machine_id,
            "name": a.name,
            "window_start_hours": iw.window_start_hours,
            "window_end_hours": iw.window_end_hours,
            "confidence": iw.confidence,
            "reason": iw.reason,
            "recommendation": iw.recommendation,
            "updated_at": iw.created_at.isoformat(),
        })
    # Sort by urgency: soonest window first
    out.sort(key=lambda x: (x["window_start_hours"] is None, x["window_start_hours"]))
    return out
