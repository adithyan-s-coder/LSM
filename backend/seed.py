"""
seed.py — populates the database with a demo user, five demo machines,
realistic historical sensor readings, thresholds, cost models, and one
failure/maintenance record each, then runs the full analysis pipeline once
per machine so the dashboard has real predictions on first login.

Run with:
    python seed.py
(from inside backend/, with the venv active and DATABASE_URL configured)
"""
import random
from datetime import datetime, timedelta

from database import Base, engine, SessionLocal
import models
from auth_utils import hash_password
from analysis_pipeline import run_full_analysis


# machine_id, name, type, risk profile, history length (hours) tuned so the
# resulting computed health score lands near the demo target for that machine
DEMO_MACHINES = [
    ("MTR-024", "CNC Motor MTR-024", "CNC Motor", "deteriorating", 105),
    ("P-102", "Pump P-102", "Centrifugal Pump", "stable", 60),
    ("C-014", "Compressor C-014", "Air Compressor", "critical", 55),
    ("H-008", "Hydraulic Unit H-008", "Hydraulic Unit", "warning", 90),
    ("F-019", "Cooling Fan F-019", "Industrial Fan", "excellent", 40),
]

PROFILES = {
    # profile: (start_temp, start_vib, start_cur, temp_drift/hr, vib_drift/hr, cur_drift/hr)
    "excellent": (55, 2.5, 8.5, 0.0, 0.0, 0.0),
    "stable": (58, 3.0, 9.0, 0.01, 0.005, 0.002),
    "warning": (65, 4.2, 10.5, 0.05, 0.02, 0.01),
    "deteriorating": (65, 4.2, 11.8, 0.13, 0.036, 0.02),
    "critical": (72, 6.5, 13.0, 0.25, 0.07, 0.03),
}


def generate_history(asset: models.Asset, profile_key: str, hours: int = 105):
    base_temp, base_vib, base_cur, dtemp, dvib, dcur = PROFILES[profile_key]
    start_time = datetime.utcnow() - timedelta(hours=hours)
    base_load = 60
    base_hours = 4000

    readings = []
    for h in range(hours):
        temp = base_temp + dtemp * h + random.gauss(0, 0.6)
        vib = base_vib + dvib * h + random.gauss(0, 0.15)
        cur = base_cur + dcur * h + random.gauss(0, 0.2)
        load = max(20, min(100, base_load + random.gauss(0, 5)))

        readings.append(models.SensorReading(
            asset_id=asset.id,
            timestamp=start_time + timedelta(hours=h),
            temperature=round(max(20, temp), 2),
            vibration=round(max(0, vib), 2),
            current_amp=round(max(0, cur), 2),
            load_pct=round(load, 2),
            operating_hours=round(base_hours + h, 1),
        ))
    return readings


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ---- Demo user ----
        if not db.query(models.User).filter(models.User.email == "admin@example.com").first():
            db.add(models.User(
                name="Demo Admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
            ))
            db.commit()
            print("Created demo user: admin@example.com / admin123")

        for machine_id, name, mtype, profile, _target_health in DEMO_MACHINES:
            asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
            if asset:
                print(f"Skipping {machine_id}, already seeded.")
                continue

            asset = models.Asset(
                machine_id=machine_id,
                name=name,
                type=mtype,
                location="Plant Floor A",
                installation_date=datetime.utcnow().date() - timedelta(days=800),
                operating_hours=4200,
                status="Normal",
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

            db.add(models.AssetThreshold(asset_id=asset.id))
            db.add(models.CostModel(asset_id=asset.id))

            # One historical failure + one maintenance record for realism
            db.add(models.FailureRecord(
                asset_id=asset.id,
                failure_date=datetime.utcnow() - timedelta(days=180),
                description="Bearing wear caused unexpected shutdown.",
                repair_cost=265000,
                production_loss=410000,
            ))
            db.add(models.MaintenanceRecord(
                asset_id=asset.id,
                maintenance_type="Scheduled inspection",
                scheduled_at=datetime.utcnow() - timedelta(days=30),
                completed_at=datetime.utcnow() - timedelta(days=30),
                cost=5200,
                downtime_hours=2,
                notes="Routine bearing lubrication and vibration check.",
                status="Completed",
            ))
            db.commit()

            readings = generate_history(asset, profile)
            db.add_all(readings)
            db.commit()

            print(f"Seeded {machine_id} with {len(readings)} readings (profile: {profile})")

            # Run the pipeline once so dashboard/predictions have real data immediately
            asset = db.query(models.Asset).filter(models.Asset.machine_id == machine_id).first()
            result = run_full_analysis(db, asset)
            if "error" not in result:
                print(
                    f"  -> health={result['health']['health_score']} "
                    f"risk={result['risk']['risk_level']} "
                    f"critical={result['critical_time']['estimated_critical_time_hours']}h"
                )

        print("\nSeed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
