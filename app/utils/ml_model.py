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
import joblib
import os
import numpy as np

# Load trained model
model_path = os.path.join(os.path.dirname(__file__), "downtime_model.pkl")
model = joblib.load(model_path)

def predict_downtime_risk(machine_id: str, avg_temp: float, avg_vibration: float, past_failures: int) -> dict:
    """
    Predicts downtime risk using trained ML model.
    """
    features = np.array([[machine_id, avg_temp, avg_vibration, past_failures]])
    prediction = model.predict(features)[0]
    risk_score = model.predict_proba(features)[0][1]  # Probability of downtime

    return {
        "machine_id": machine_id,
        "risk_score": round(risk_score, 2),
        "status": "High" if risk_score > 0.7 else "Low",
        "prediction": "Downtime Expected" if prediction == 1 else "No Downtime"
    }
