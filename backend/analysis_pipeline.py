"""
analysis_pipeline.py

Wires together the full pipeline described in the spec:

Machine Data -> Anomaly Detection -> Deterioration Analysis -> Health Score
-> Critical-Time/RUL Estimation -> Last-Safe-Moment Engine
-> Cost & Risk Analysis -> Recommendation -> stored Prediction / Intervention Window

Called by routers whenever readings change (upload, simulation) and when a
fresh analysis is requested for an asset.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ml.anomaly_detection import detect_anomalies, latest_anomaly_summary
from ml.deterioration_analysis import analyze_deterioration
from ml.health_score import calculate_health_score
from ml.rul_estimator import estimate_critical_time
from ml.last_safe_moment_engine import calculate_last_safe_moment
from ml.risk_engine import calculate_risk
from ml.cost_engine import estimate_cost_of_waiting
from ml.recommendation_engine import build_reasons, recommend_action

import models


def _readings_to_dicts(readings) -> List[Dict]:
    return [
        {
            "timestamp": r.timestamp,
            "temperature": r.temperature,
            "vibration": r.vibration,
            "current_amp": r.current_amp,
            "load_pct": r.load_pct,
        }
        for r in readings
    ]


def run_full_analysis(db: Session, asset: "models.Asset") -> Dict:
    """
    Runs the entire pipeline for one asset using its stored sensor_readings,
    persists a new Prediction + InterventionWindow, and returns a rich dict
    ready to hand back to the frontend.
    """
    readings = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.asset_id == asset.id)
        .order_by(models.SensorReading.timestamp.asc())
        .all()
    )
    data = _readings_to_dicts(readings)

    if not data:
        return {"error": "No sensor readings available for this asset yet."}

    # 1. Anomaly detection
    anomaly_flagged = detect_anomalies(list(data))
    anomaly_summary = latest_anomaly_summary(list(data))

    # 2. Health score (current + a short rolling series for trend context)
    window = anomaly_flagged[-50:] if len(anomaly_flagged) > 50 else anomaly_flagged
    health_result = calculate_health_score(window)
    health_score = health_result["health_score"]

    # Build a health series across the window for deterioration slope input
    health_series = []
    step = max(1, len(window) // 20)
    for i in range(0, len(window), step):
        sub = window[: i + 1]
        health_series.append(calculate_health_score(sub)["health_score"])
    if len(health_series) < len(window[::step]):
        health_series.append(health_score)

    previous_health = health_series[0] if health_series else health_score

    # 3. Deterioration analysis
    deterioration = analyze_deterioration(window, health_series if len(health_series) == len(window[::step]) + (1 if len(window) % step else 0) else None)
    # Fallback simple recompute if lengths mismatched (keeps pipeline robust)
    if deterioration.get("health_slope_per_hour", 0) == 0.0 and len(window) >= 2:
        t0 = window[0]["timestamp"]
        hours_span = max((window[-1]["timestamp"] - t0).total_seconds() / 3600.0, 0.01)
        deterioration["health_slope_per_hour"] = round((health_score - previous_health) / hours_span, 4)

    # 4. Critical time / RUL estimation
    threshold = asset.thresholds.critical_health_threshold if asset.thresholds else 45.0
    rul = estimate_critical_time(
        current_health=health_score,
        health_slope_per_hour=deterioration["health_slope_per_hour"],
        critical_threshold=threshold,
        data_points=len(window),
    )

    # 5. Risk engine
    risk = calculate_risk(
        health_score=health_score,
        anomaly_rate=anomaly_summary["anomaly_rate"],
        severity_score=deterioration.get("severity_score", 0),
        critical_time_hours=rul["estimated_critical_time_hours"],
    )

    # 6. Reasons + recommendation
    reasons = build_reasons(
        vibration_slope=deterioration["vibration_slope_per_hour"],
        temperature_slope=deterioration["temperature_slope_per_hour"],
        health_score=health_score,
        previous_health=previous_health,
        deterioration_label=deterioration["deterioration_label"],
        critical_time_hours=rul["estimated_critical_time_hours"],
    )

    # 7. Last-Safe-Moment engine
    lsm = calculate_last_safe_moment(
        critical_time_hours=rul["estimated_critical_time_hours"],
        range_low_hours=rul["range_low_hours"],
        range_high_hours=rul["range_high_hours"],
        confidence=rul["confidence"],
        risk_level=risk["risk_level"],
        reasons=reasons,
    )

    action = recommend_action(
        risk_level=risk["risk_level"],
        machine_name=asset.name,
        window_start=lsm["intervention_start"],
        window_end=lsm["intervention_end"],
    )

    # 8. Cost engine
    cost_row = db.query(models.CostModel).filter(models.CostModel.asset_id == asset.id).first()
    cost_overrides = None
    if cost_row:
        cost_overrides = {
            "hourly_downtime_cost": cost_row.hourly_downtime_cost,
            "emergency_repair_cost": cost_row.emergency_repair_cost,
            "production_loss_per_incident": cost_row.production_loss_per_incident,
            "routine_maintenance_cost": cost_row.routine_maintenance_cost,
            "delayed_maintenance_cost": cost_row.delayed_maintenance_cost,
        }
    cost = estimate_cost_of_waiting(risk["risk_level"], cost_overrides)

    # ---- Persist Prediction ----
    prediction = models.Prediction(
        asset_id=asset.id,
        health_score=health_score,
        risk_level=risk["risk_level"],
        critical_time_hours=rul["estimated_critical_time_hours"],
        confidence=rul["confidence"],
        deterioration_rate=deterioration["health_slope_per_hour"],
        reasons="; ".join(reasons),
    )
    db.add(prediction)
    db.flush()

    if lsm["intervention_start"] is not None:
        iw = models.InterventionWindow(
            asset_id=asset.id,
            prediction_id=prediction.id,
            window_start_hours=lsm["intervention_start"],
            window_end_hours=lsm["intervention_end"],
            confidence=rul["confidence"],
            reason="; ".join(reasons),
            recommendation=action["headline"],
        )
        db.add(iw)

    # Update asset status + operating hours snapshot
    asset.status = deterioration["deterioration_label"]
    db.add(asset)

    # Auto-generate an alert for HIGH/CRITICAL risk
    if risk["risk_level"] in ("HIGH", "CRITICAL"):
        alert = models.Alert(
            asset_id=asset.id,
            severity="Critical" if risk["risk_level"] == "CRITICAL" else "High",
            title=f"{risk['risk_level']} RISK — {asset.name} entering intervention window",
            message=action["headline"],
        )
        db.add(alert)

    db.commit()

    latest_reading = readings[-1]

    return {
        "machine_id": asset.machine_id,
        "machine_name": asset.name,
        "latest_reading": {
            "temperature": latest_reading.temperature,
            "vibration": latest_reading.vibration,
            "current": latest_reading.current_amp,
            "load": latest_reading.load_pct,
            "timestamp": latest_reading.timestamp.isoformat(),
        },
        "health": health_result,
        "anomaly": anomaly_summary,
        "deterioration": deterioration,
        "critical_time": rul,
        "risk": risk,
        "last_safe_moment": lsm,
        "recommendation": action,
        "cost_analysis": cost,
        "reasons": reasons,
    }
