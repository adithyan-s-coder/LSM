"""Pydantic request/response schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_email: str


# ---------- Assets ----------
class AssetCreate(BaseModel):
    machine_id: str
    name: str
    type: str
    location: Optional[str] = None
    installation_date: Optional[date] = None
    operating_hours: Optional[float] = 0


class AssetOut(BaseModel):
    id: int
    machine_id: str
    name: str
    type: str
    location: Optional[str]
    operating_hours: float
    status: str

    class Config:
        orm_mode = True


# ---------- Sensor Readings ----------
class SensorReadingIn(BaseModel):
    timestamp: datetime
    machine_id: str
    temperature: float
    vibration: float
    current: float
    load: float
    operating_hours: float


# ---------- Simulation ----------
class SimulationRequest(BaseModel):
    machine_id: str
    scenario: str  # Healthy, Temporary Anomaly, Gradual Deterioration, Rapid Deterioration, Near Failure
    duration_hours: int = 48
    severity: str = "medium"  # low, medium, high


# ---------- Maintenance ----------
class MaintenanceCreate(BaseModel):
    machine_id: str
    maintenance_type: str
    scheduled_at: Optional[datetime] = None
    cost: Optional[float] = 0
    downtime_hours: Optional[float] = 0
    notes: Optional[str] = None
    status: Optional[str] = "Recommended"


class MaintenanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    cost: Optional[float] = None
    downtime_hours: Optional[float] = None
    completed_at: Optional[datetime] = None
