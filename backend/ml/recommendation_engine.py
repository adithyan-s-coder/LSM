"""
recommendation_engine.py
Turns risk level + deterioration signals into a concrete recommended action
and a human-readable reason, in plain language, not "AI says maintenance required".
"""
from typing import Dict, List


ACTIONS_BY_RISK = {
    "LOW": "Continue monitoring",
    "MEDIUM": "Inspect machine",
    "HIGH": "Schedule maintenance",
    "CRITICAL": "Immediate shutdown / emergency intervention",
}


def build_reasons(
    vibration_slope: float,
    temperature_slope: float,
    health_score: float,
    previous_health: float,
    deterioration_label: str,
    critical_time_hours,
) -> List[str]:
    reasons = []
    if vibration_slope > 0.02:
        pct_note = ""
        if previous_health:
            pct_note = ""
        reasons.append(f"Vibration is trending upward (~{round(vibration_slope, 3)} mm/s per hour).")
    if temperature_slope > 0.02:
        reasons.append(f"Temperature is trending upward (~{round(temperature_slope, 3)}°C per hour).")
    if previous_health and previous_health > health_score:
        drop = round(previous_health - health_score, 1)
        reasons.append(
            f"Machine health has decreased from {round(previous_health,1)}% to {round(health_score,1)}% ({drop} pt drop)."
        )
    if deterioration_label in ("Gradual deterioration", "Rapid deterioration"):
        reasons.append(f"Deterioration rate is classified as '{deterioration_label}'.")
    if critical_time_hours is not None:
        reasons.append(f"Estimated critical condition is approximately {critical_time_hours} hours away.")
    reasons.append("Waiting increases the estimated cost and downtime of intervention.")
    return reasons


def recommend_action(risk_level: str, machine_name: str, window_start: float = None, window_end: float = None) -> Dict:
    action = ACTIONS_BY_RISK.get(risk_level, "Continue monitoring")

    if window_start is not None and window_end is not None and risk_level in ("HIGH", "CRITICAL"):
        headline = f"Inspect {machine_name} within {window_start:.0f}\u2013{window_end:.0f} hours."
    else:
        headline = f"{action} for {machine_name}."

    return {"recommended_action": action, "headline": headline}
