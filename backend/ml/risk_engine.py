"""
risk_engine.py
Combines health, anomaly severity, deterioration rate, and estimated
critical time into a single LOW / MEDIUM / HIGH / CRITICAL risk level.
"""
from typing import Dict, Optional


def calculate_risk(
    health_score: float,
    anomaly_rate: float,
    severity_score: int,
    critical_time_hours: Optional[float],
) -> Dict:
    """
    health_score: 0-100
    anomaly_rate: 0-1, share of recent readings flagged anomalous
    severity_score: 0-6 from deterioration_analysis
    critical_time_hours: hours until projected critical condition, or None
    """
    points = 0

    if health_score < 40:
        points += 4
    elif health_score < 60:
        points += 3
    elif health_score < 75:
        points += 1

    points += min(3, round(anomaly_rate * 3))

    points += min(3, severity_score // 2)

    if critical_time_hours is not None:
        if critical_time_hours <= 24:
            points += 4
        elif critical_time_hours <= 72:
            points += 2
        elif critical_time_hours <= 168:
            points += 1

    if points >= 9:
        level = "CRITICAL"
    elif points >= 6:
        level = "HIGH"
    elif points >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"risk_level": level, "risk_points": points}
