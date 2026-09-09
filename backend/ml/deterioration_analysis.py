"""
deterioration_analysis.py
Computes rate-of-change (slope) for each sensor and for health over time,
using ordinary least squares trend fitting on the recent reading history.
"""
from typing import List, Dict
import numpy as np


def _hourly_slope(timestamps_hours: List[float], values: List[float]) -> float:
    """Linear regression slope in units-per-hour."""
    if len(values) < 2:
        return 0.0
    x = np.array(timestamps_hours, dtype=float)
    y = np.array(values, dtype=float)
    if np.allclose(x, x[0]):
        return 0.0
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def analyze_deterioration(readings: List[Dict], health_series: List[float] = None) -> Dict:
    """
    readings: oldest->newest, each with 'timestamp' (datetime) and sensor fields.
    health_series: optional parallel list of health scores per reading.

    Returns per-hour slopes for temperature, vibration, current, load, and
    (if provided) health, plus a qualitative deterioration label.
    """
    if len(readings) < 2:
        return {
            "temperature_slope_per_hour": 0.0,
            "vibration_slope_per_hour": 0.0,
            "current_slope_per_hour": 0.0,
            "load_slope_per_hour": 0.0,
            "health_slope_per_hour": 0.0,
            "deterioration_label": "Insufficient data",
        }

    t0 = readings[0]["timestamp"]
    hours = [(r["timestamp"] - t0).total_seconds() / 3600.0 for r in readings]

    temp_slope = _hourly_slope(hours, [r.get("temperature", 0) for r in readings])
    vib_slope = _hourly_slope(hours, [r.get("vibration", 0) for r in readings])
    cur_slope = _hourly_slope(hours, [r.get("current_amp", 0) for r in readings])
    load_slope = _hourly_slope(hours, [r.get("load_pct", 0) for r in readings])

    health_slope = 0.0
    if health_series and len(health_series) == len(readings):
        health_slope = _hourly_slope(hours, health_series)

    # Qualitative label based on how fast vibration/temperature are rising
    # and health is falling.
    severity = 0
    if vib_slope > 0.15:
        severity += 2
    elif vib_slope > 0.05:
        severity += 1
    if temp_slope > 0.3:
        severity += 2
    elif temp_slope > 0.1:
        severity += 1
    if health_slope < -0.5:
        severity += 2
    elif health_slope < -0.15:
        severity += 1

    if severity >= 5:
        label = "Rapid deterioration"
    elif severity >= 3:
        label = "Gradual deterioration"
    elif severity >= 1:
        label = "Mild deterioration"
    else:
        label = "Stable"

    return {
        "temperature_slope_per_hour": round(temp_slope, 4),
        "vibration_slope_per_hour": round(vib_slope, 4),
        "current_slope_per_hour": round(cur_slope, 4),
        "load_slope_per_hour": round(load_slope, 4),
        "health_slope_per_hour": round(health_slope, 4),
        "deterioration_label": label,
        "severity_score": severity,
    }
