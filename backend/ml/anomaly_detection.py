"""
anomaly_detection.py
Uses scikit-learn's IsolationForest to flag abnormal sensor readings.

This is a real, fitted model (not randomly generated results): it is trained
on the machine's own historical readings each time it's invoked, so it adapts
to that machine's normal operating pattern.
"""
from typing import List, Dict
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["temperature", "vibration", "current_amp", "load_pct"]


def detect_anomalies(readings: List[Dict], contamination: float = 0.1) -> List[Dict]:
    """
    readings: list of dicts with FEATURES keys, oldest->newest.
    Returns the same list with 'is_anomaly' (bool) and 'anomaly_score' (float,
    higher = more anomalous) added to each row.

    Requires a minimum number of samples to fit a meaningful model; if there
    isn't enough history yet, everything is marked normal with score 0.
    """
    if len(readings) < 10:
        for r in readings:
            r["is_anomaly"] = False
            r["anomaly_score"] = 0.0
        return readings

    X = np.array([[r.get(f, 0.0) or 0.0 for f in FEATURES] for r in readings])

    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
    )
    model.fit(X)

    raw_scores = model.decision_function(X)   # higher = more normal
    predictions = model.predict(X)             # -1 = anomaly, 1 = normal

    # Convert decision_function output into an intuitive 0-1 "anomaly score"
    # where higher means more anomalous.
    min_s, max_s = raw_scores.min(), raw_scores.max()
    span = max(max_s - min_s, 1e-6)
    normalized = 1 - ((raw_scores - min_s) / span)

    for r, pred, score in zip(readings, predictions, normalized):
        r["is_anomaly"] = bool(pred == -1)
        r["anomaly_score"] = round(float(score), 3)

    return readings


def latest_anomaly_summary(readings: List[Dict]) -> Dict:
    """Summarize anomaly state for the most recent window of readings."""
    if not readings:
        return {"anomaly_count": 0, "anomaly_rate": 0.0, "latest_is_anomaly": False}

    flagged = detect_anomalies(readings)
    anomaly_count = sum(1 for r in flagged if r.get("is_anomaly"))
    return {
        "anomaly_count": anomaly_count,
        "anomaly_rate": round(anomaly_count / len(flagged), 3),
        "latest_is_anomaly": bool(flagged[-1].get("is_anomaly")),
        "latest_score": flagged[-1].get("anomaly_score", 0.0),
    }
