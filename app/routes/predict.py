# app/routes/predict.py
from fastapi import APIRouter
from app.ml.model import predict_downtime

router = APIRouter()

@router.post("/predict")
def predict_downtime_api(temperature: float, vibration: float, load: float):
    prediction = predict_downtime(temperature, vibration, load)
    return {
        "temperature": temperature,
        "vibration": vibration,
        "load": load,
        "downtime_predicted": bool(prediction)
    }
