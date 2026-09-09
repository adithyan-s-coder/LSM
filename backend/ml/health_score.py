"""
health_score.py
Calculates a 0-100 machine health score from recent sensor readings.

The score blends:
  - how far each sensor sits above its "normal" operating band
  - the short-term trend (slope) of each sensor
into a single explainable number. This is intentionally simple/transparent
rather than a black-box model, per the project's honesty requirement.
"""
from typing import List, Dict
import numpy as np

# Reasonable "normal" operating bands for the demo sensors.
# Real deployments should source these from asset_thresholds per machine.
NORMAL_RANGES = {
    "temperature": (40, 70),   # deg C
    "vibration": (0, 5.0),     # mm/s
    "current_amp": (5, 12),    # A
    "load_pct": (30, 80),      # %
}

WEIGHTS = {
    "temperature": 0.25,
    "vibration": 0.35,
    "current_amp": 0.20,
    "load_pct": 0.10,
    "trend": 0.10,
}


def _band_score(value: float, low: float, high: float) -> float:
    """
    Returns 100 if value is within [low, high].
    Degrades linearly as value moves outside the band, floored at 0.
    """
    if value is None:
        return 100.0
    if low <= value <= high:
        return 100.0
    span = max(high - low, 1e-6)
    if value > high:
        overshoot = (value - high) / span
    else:
        overshoot = (low - value) / span
    score = 100.0 - min(overshoot, 1.0) * 100.0 * 1.2
    return max(0.0, score)


def _slope(values: List[float]) -> float:
    """Simple linear regression slope over index (per-sample rate of change)."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    y = np.array(values, dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def calculate_health_score(readings: List[Dict]) -> Dict:
    """
    readings: list of dicts sorted oldest->newest, each with keys:
        temperature, vibration, current_amp, load_pct
    Returns dict with overall score, per-sensor sub-scores, and status label.
    """
    if not readings:
        return {
            "health_score": 100.0,
            "status": "Excellent",
            "sub_scores": {},
            "note": "No readings available; defaulting to baseline health.",
        }

    latest = readings[-1]

    sub_scores = {}
    for sensor, (low, high) in NORMAL_RANGES.items():
        val = latest.get(sensor)
        sub_scores[sensor] = round(_band_score(val, low, high), 1)

    # Trend penalty: worsening vibration/temperature trend reduces score further
    vib_series = [r.get("vibration") for r in readings if r.get("vibration") is not None]
    temp_series = [r.get("temperature") for r in readings if r.get("temperature") is not None]
    vib_slope = _slope(vib_series)
    temp_slope = _slope(temp_series)

    # Normalize slope impact into a 0-100 "trend score" (100 = stable/improving)
    trend_penalty = max(0.0, vib_slope) * 8 + max(0.0, temp_slope) * 3
    trend_score = max(0.0, 100.0 - trend_penalty * 10)

    weighted = (
        sub_scores["temperature"] * WEIGHTS["temperature"]
        + sub_scores["vibration"] * WEIGHTS["vibration"]
        + sub_scores["current_amp"] * WEIGHTS["current_amp"]
        + sub_scores["load_pct"] * WEIGHTS["load_pct"]
        + trend_score * WEIGHTS["trend"]
    )
    health = round(max(0.0, min(100.0, weighted)), 1)

    if health >= 90:
        status = "Excellent"
    elif health >= 75:
        status = "Good"
    elif health >= 60:
        status = "Warning"
    elif health >= 40:
        status = "Poor"
    else:
        status = "Critical"

    return {
        "health_score": health,
        "status": status,
        "sub_scores": sub_scores,
        "trend_score": round(trend_score, 1),
        "vibration_slope_per_sample": round(vib_slope, 4),
        "temperature_slope_per_sample": round(temp_slope, 4),
    }
