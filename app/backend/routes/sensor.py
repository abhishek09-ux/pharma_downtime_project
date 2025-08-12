
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.downtime import Downtime
from app.ml.model import predict_downtime


router = APIRouter()


@router.post("/sensor-data/")
def receive_sensor_data(machine_temperature: float, vibration_level: float, humidity: float, shift_time: int, db: Session = Depends(get_db)):
    # Prepare features for model
    features = [machine_temperature, vibration_level, humidity, shift_time]
    
    # Predict downtime
    import joblib
    import numpy as np
    try:
        model = joblib.load("backend/model/downtime_predictor.pkl")
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(np.array(features).reshape(1, -1))[0][1]
        else:
            probability = float(model.predict(np.array(features).reshape(1, -1))[0])
    except Exception as e:
        probability = None
        return {"status": "error", "detail": str(e)}

    # Store in DB
    event = Downtime(
        machine_id="sensor", # or pass as param if available
        reason="Sensor data",
        duration_minutes=0.0,
        timestamp=None # will default to now
    )
    db.add(event)
    db.commit()

    return {"status": "success", "downtime_probability": probability}

# If you want to send alerts, uncomment and implement send_alert in app/utils/alerts.py
# from app.utils.alerts import send_alert

# Single endpoint definition using Downtime ORM model
@router.post("/sensor-data/")
def receive_sensor_data(machine_temperature: float, vibration_level: float, humidity: float, shift_time: int, db: Session = Depends(get_db)):
    features = [machine_temperature, vibration_level, humidity, shift_time]
    import joblib
    import numpy as np
    try:
        model = joblib.load("backend/model/downtime_predictor.pkl")
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(np.array(features).reshape(1, -1))[0][1]
        else:
            probability = float(model.predict(np.array(features).reshape(1, -1))[0])
    except Exception as e:
        probability = None
        return {"status": "error", "detail": str(e)}

    # Store in DB
    event = Downtime(
        machine_id="sensor", # or pass as param if available
        reason="Sensor data",
        duration_minutes=0.0,
        timestamp=None # will default to now
    )
    db.add(event)
    db.commit()

    # 🚨 Trigger alert if probability high
    # if probability is not None and probability > 0.7:
    #     send_alert(machine_temperature, vibration_level, probability)

    return {"status": "success", "downtime_probability": probability}
