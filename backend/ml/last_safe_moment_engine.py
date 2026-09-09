"""
last_safe_moment_engine.py

The central decision-support calculation of the application.

It does NOT just return the estimated failure/critical time. It works
backward from that critical time using operational, safety, and cost
constraints to recommend an EARLIER window in which intervention is both
safe and economically sensible — and explains why that window was chosen.
"""
from typing import Dict, List, Optional


def calculate_last_safe_moment(
    critical_time_hours: Optional[float],
    range_low_hours: Optional[float],
    range_high_hours: Optional[float],
    confidence: float,
    risk_level: str,
    maintenance_duration_hours: float = 4.0,
    safety_margin_fraction: float = 0.35,
    reasons: Optional[List[str]] = None,
) -> Dict:
    """
    critical_time_hours: point estimate of hours until critical condition
    range_low_hours / range_high_hours: uncertainty band around that estimate
    confidence: 0-100
    risk_level: LOW / MEDIUM / HIGH / CRITICAL
    maintenance_duration_hours: how long the intervention itself will take
    safety_margin_fraction: fraction of the remaining time held back as a
        safety buffer, so we don't recommend acting right at the edge of
        the critical estimate

    The recommended window is deliberately EARLIER than the raw critical-time
    estimate: we subtract (a) the time the maintenance itself will consume,
    and (b) a safety margin that widens with uncertainty and risk, so the
    team still has slack if deterioration accelerates.
    """
    reasons = list(reasons or [])

    if critical_time_hours is None:
        return {
            "estimated_critical_time": None,
            "intervention_start": None,
            "intervention_end": None,
            "confidence": confidence,
            "risk": risk_level,
            "reason": reasons + ["No near-term critical condition projected from current trend."],
            "recommendation_summary": "No intervention window required at this time; continue monitoring.",
        }

    # Widen the safety margin for higher risk / lower confidence, since we
    # trust the estimate less and want more buffer.
    risk_margin_boost = {"LOW": 0.0, "MEDIUM": 0.05, "HIGH": 0.12, "CRITICAL": 0.20}.get(risk_level, 0.05)
    confidence_penalty = max(0.0, (85 - confidence) / 100.0) * 0.3
    effective_margin = min(0.6, safety_margin_fraction + risk_margin_boost + confidence_penalty)

    safe_low = (range_low_hours if range_low_hours is not None else critical_time_hours) * (1 - effective_margin)
    safe_high = (range_high_hours if range_high_hours is not None else critical_time_hours) * (1 - effective_margin)

    # Ensure maintenance itself fits comfortably before the critical point.
    intervention_end = max(0.0, safe_high - maintenance_duration_hours)
    intervention_start = max(0.0, safe_low - maintenance_duration_hours)

    if intervention_start > intervention_end:
        intervention_start, intervention_end = intervention_end, intervention_start

    reasons.append(
        f"Intervention window is set earlier than the {round(critical_time_hours,1)}h critical estimate "
        f"to allow for a {round(effective_margin*100)}% safety margin plus "
        f"{maintenance_duration_hours}h of maintenance time."
    )

    return {
        "estimated_critical_time": round(critical_time_hours, 1),
        "intervention_start": round(intervention_start, 1),
        "intervention_end": round(intervention_end, 1),
        "confidence": confidence,
        "risk": risk_level,
        "reason": reasons,
        "recommendation_summary": (
            f"Estimated last safe intervention window: "
            f"{round(intervention_start,1)}\u2013{round(intervention_end,1)} hours from now."
        ),
    }
