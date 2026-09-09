from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import MaintenanceCreate, MaintenanceUpdate
from auth_utils import get_current_user

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("")
def list_maintenance(db: Session = Depends(get_db), user=Depends(get_current_user)):
    records = db.query(models.MaintenanceRecord).order_by(models.MaintenanceRecord.created_at.desc()).all()
    out = []
    for r in records:
        asset = db.query(models.Asset).get(r.asset_id)
        out.append({
            "id": r.id,
            "machine_id": asset.machine_id if asset else None,
            "machine_name": asset.name if asset else None,
            "maintenance_type": r.maintenance_type,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "cost": r.cost,
            "downtime_hours": r.downtime_hours,
            "notes": r.notes,
            "status": r.status,
        })
    return out


@router.post("")
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    asset = db.query(models.Asset).filter(models.Asset.machine_id == payload.machine_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    record = models.MaintenanceRecord(
        asset_id=asset.id,
        maintenance_type=payload.maintenance_type,
        scheduled_at=payload.scheduled_at,
        cost=payload.cost,
        downtime_hours=payload.downtime_hours,
        notes=payload.notes,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "status": "created"}


@router.put("/{record_id}")
def update_maintenance(record_id: int, payload: MaintenanceUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    record = db.query(models.MaintenanceRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(record, field, value)
    db.add(record)
    db.commit()
    return {"id": record.id, "status": "updated"}
