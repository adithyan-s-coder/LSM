from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).limit(200).all()
    out = []
    for a in alerts:
        asset = db.query(models.Asset).get(a.asset_id)
        out.append({
            "id": a.id,
            "machine_id": asset.machine_id if asset else None,
            "machine_name": asset.name if asset else None,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "is_read": bool(a.is_read),
            "created_at": a.created_at.isoformat(),
        })
    return out


@router.put("/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    alert = db.query(models.Alert).get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = 1
    db.add(alert)
    db.commit()
    return {"id": alert.id, "status": "read"}
