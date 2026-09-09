"""SQLAlchemy ORM models mirroring database/schema.sql"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Text, DateTime, Date,
    ForeignKey, SmallInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    type = Column(String(80), nullable=False)
    location = Column(String(150))
    installation_date = Column(Date)
    operating_hours = Column(Float, default=0)
    status = Column(String(30), default="Normal")
    created_at = Column(DateTime, server_default=func.now())

    thresholds = relationship("AssetThreshold", backref="asset", uselist=False)
    readings = relationship("SensorReading", backref="asset")
    maintenance = relationship("MaintenanceRecord", backref="asset")
    failures = relationship("FailureRecord", backref="asset")
    predictions = relationship("Prediction", backref="asset")
    alerts = relationship("Alert", backref="asset")


class AssetThreshold(Base):
    __tablename__ = "asset_thresholds"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    temperature_limit = Column(Float, default=90)
    vibration_limit = Column(Float, default=10)
    current_limit = Column(Float, default=18)
    load_limit = Column(Float, default=100)
    critical_health_threshold = Column(Float, default=45)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float)
    vibration = Column(Float)
    current_amp = Column(Float)
    load_pct = Column(Float)
    operating_hours = Column(Float)
    is_anomaly = Column(SmallInteger, default=0)
    anomaly_score = Column(Float, default=0)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    maintenance_type = Column(String(100))
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    cost = Column(Float, default=0)
    downtime_hours = Column(Float, default=0)
    notes = Column(Text)
    status = Column(String(30), default="Recommended")
    created_at = Column(DateTime, server_default=func.now())


class FailureRecord(Base):
    __tablename__ = "failure_records"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    failure_date = Column(DateTime)
    description = Column(Text)
    repair_cost = Column(Float, default=0)
    production_loss = Column(Float, default=0)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    health_score = Column(Float)
    risk_level = Column(String(20))
    critical_time_hours = Column(Float)
    confidence = Column(Float)
    deterioration_rate = Column(Float)
    reasons = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    intervention_windows = relationship("InterventionWindow", backref="prediction")


class InterventionWindow(Base):
    __tablename__ = "intervention_windows"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    window_start_hours = Column(Float)
    window_end_hours = Column(Float)
    confidence = Column(Float)
    reason = Column(Text)
    recommendation = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    severity = Column(String(20))
    title = Column(String(200))
    message = Column(Text)
    is_read = Column(SmallInteger, default=0)
    created_at = Column(DateTime, server_default=func.now())


class CostModel(Base):
    __tablename__ = "cost_models"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=True)
    hourly_downtime_cost = Column(Float, default=2500)
    emergency_repair_cost = Column(Float, default=280000)
    production_loss_per_incident = Column(Float, default=520000)
    routine_maintenance_cost = Column(Float, default=5000)
    delayed_maintenance_cost = Column(Float, default=48000)
