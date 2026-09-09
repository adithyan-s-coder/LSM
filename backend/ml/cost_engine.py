"""
cost_engine.py
Estimates the financial impact of acting now vs. waiting vs. failure,
based on cost assumptions stored in the cost_models table (with sane
fallback defaults). All figures are clearly demonstration estimates.
"""
from typing import Dict


DEFAULT_COSTS = {
    "hourly_downtime_cost": 2500,
    "emergency_repair_cost": 280000,
    "production_loss_per_incident": 520000,
    "routine_maintenance_cost": 5000,
    "delayed_maintenance_cost": 48000,
}


def estimate_cost_of_waiting(risk_level: str, cost_model: Dict = None) -> Dict:
    """
    Returns an "Act Now" vs "Wait" vs "Failure" cost/downtime/risk comparison.
    cost_model: dict of overrides sourced from the cost_models table.
    """
    c = {**DEFAULT_COSTS, **(cost_model or {})}

    risk_multiplier = {
        "LOW": 0.6,
        "MEDIUM": 1.0,
        "HIGH": 1.3,
        "CRITICAL": 1.6,
    }.get(risk_level, 1.0)

    act_now = {
        "maintenance_cost": round(c["routine_maintenance_cost"]),
        "downtime_hours": 2,
        "risk": "Low",
    }
    wait = {
        "maintenance_cost": round(c["delayed_maintenance_cost"] * risk_multiplier),
        "downtime_hours": 8,
        "risk": "Medium/High",
    }
    failure = {
        "repair_cost": round(c["emergency_repair_cost"] * risk_multiplier),
        "production_loss": round(c["production_loss_per_incident"] * risk_multiplier),
        "total_impact": round(
            (c["emergency_repair_cost"] + c["production_loss_per_incident"]) * risk_multiplier
        ),
    }

    return {"act_now": act_now, "wait": wait, "failure": failure}
