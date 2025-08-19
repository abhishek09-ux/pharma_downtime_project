# app/routes/predict.py
from fastapi import APIRouter, HTTPException
import pickle
import numpy as np
from typing import Dict, Any

router = APIRouter()

@router.get("/predict")
def predict_downtime_api(temperature: float, vibration: float, load: float, shift: int) -> Dict[str, Any]:
    try:
        with open("app/ml/downtime_model.pkl", "rb") as f:
            model = pickle.load(f)
        features: list[float | int] = [temperature, vibration, load, shift]
        feature_array = np.array(features).reshape(1, -1)
        
        if hasattr(model, 'predict_proba'):
            prob_result = model.predict_proba(feature_array)
            prob = float(prob_result[0][1])
            pred_result = model.predict(feature_array)
            pred = pred_result[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_probability": round(prob, 2),
                "downtime_predicted": bool(pred)
            }
        else:
            pred_array = model.predict(feature_array)
            pred_final = pred_array[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_predicted": bool(pred_final)
            }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
