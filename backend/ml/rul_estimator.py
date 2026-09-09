"""
rul_estimator.py
Estimates time-to-critical-condition ("critical time") by projecting the
current health trend forward until it crosses the machine's critical health
threshold. This is a simple, explainable linear projection — explicitly NOT
presented as an exact prediction; a confidence and a range are always
attached.
"""
from typing import Dict


def estimate_critical_time(
    current_health: float,
    health_slope_per_hour: float,
    critical_threshold: float = 45.0,
    data_points: int = 20,
) -> Dict:
    """
    current_health: latest computed health score (0-100)
    health_slope_per_hour: rate of health change per hour (negative = declining)
    critical_threshold: health score considered "critical condition"
    data_points: number of recent readings used, for confidence estimation

    Returns estimated hours until critical threshold is crossed, an
    uncertainty range, and a confidence percentage.
    """
    if health_slope_per_hour >= -0.001:
        # Flat or improving trend: no near-term critical crossing.
        return {
            "estimated_critical_time_hours": None,
            "range_low_hours": None,
            "range_high_hours": None,
            "confidence": 95 if data_points >= 15 else 70,
            "note": "Health is stable or improving; no near-term critical condition projected.",
        }

    hours_to_critical = (current_health - critical_threshold) / abs(health_slope_per_hour)
    hours_to_critical = max(0.0, hours_to_critical)

    # Uncertainty widens the fewer data points we have and the further out
    # the projection is (linear extrapolation compounds error over time).
    uncertainty_fraction = 0.25 if data_points < 15 else 0.15
    uncertainty_fraction += min(0.15, hours_to_critical / 500.0)

    low = round(hours_to_critical * (1 - uncertainty_fraction), 1)
    high = round(hours_to_critical * (1 + uncertainty_fraction), 1)

    # Confidence: more data points and a clearer (steeper, more consistent)
    # trend => higher confidence, capped in a realistic band.
    base_confidence = 90 - (uncertainty_fraction * 100)
    confidence = round(max(50.0, min(95.0, base_confidence + min(data_points, 30) * 0.3)), 0)

    return {
        "estimated_critical_time_hours": round(hours_to_critical, 1),
        "range_low_hours": low,
        "range_high_hours": high,
        "confidence": confidence,
        "note": "Linear projection of current deterioration trend against the critical health threshold.",
    }
