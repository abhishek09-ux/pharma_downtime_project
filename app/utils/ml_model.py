import random

def predict_downtime_risk(machine_id: str) -> dict:
    """
    Mock AI model for downtime prediction.
    Returns a random risk score between 0 and 1.
    """
    risk_score = round(random.uniform(0, 1), 2)
    return {
        "machine_id": machine_id,
        "risk_score": risk_score,
        "status": "High" if risk_score > 0.7 else "Low"
    }
