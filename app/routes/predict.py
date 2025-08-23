# app/routes/predict.py
from fastapi import APIRouter, HTTPException
from app.ml.model import predict_downtime
from typing import Dict, Any
import logging
import pandas as pd

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/predict")
def predict_downtime_api(
    ambient_temp: float, 
    machine_temp: float, 
    humidity: float, 
    vibration: float, 
    current: float, 
    shift: int
) -> Dict[str, Any]:
    """
    Predict downtime probability using enhanced ML model
    
    Parameters:
    - ambient_temp: Ambient temperature in °C (20-30 normal)
    - machine_temp: Machine temperature in °C (65-85 normal)
    - humidity: Relative humidity % (45-65 optimal)
    - vibration: Vibration in G (0.5-2.5 normal)
    - current: Current in Amps (2-6 normal)
    - shift: Shift number (1=day, 2=evening, 3=night)
    """
    try:
        # Use the enhanced ML model
        result = predict_downtime(ambient_temp, machine_temp, humidity, vibration, current, shift)
        
        # Add input parameters to response
        response = {
            "input_parameters": {
                "ambient_temperature": ambient_temp,
                "machine_temperature": machine_temp,
                "humidity": humidity,
                "vibration": vibration,
                "current": current,
                "shift": shift
            },
            "prediction": result,
            "model_version": "enhanced_pharma_v2.0"
        }
        
        logger.info(f"Prediction: {result['risk_level']} risk ({result['downtime_probability']:.3f})")
        return response
        
    except Exception as e:
        logger.error(f"Prediction API error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Legacy endpoint for backward compatibility
@router.get("/predict/legacy")
def predict_downtime_legacy_api(
    temperature: float, 
    vibration: float, 
    load: float, 
    shift: int
) -> Dict[str, Any]:
    """Legacy prediction endpoint - maps old parameters to new model"""
    try:
        # Map legacy parameters to new model
        ambient_temp = temperature
        machine_temp = temperature + 50  # Estimate machine temp
        humidity = 55.0  # Default humidity
        current = load / 15.0  # Estimate current from load
        
        result = predict_downtime(ambient_temp, machine_temp, humidity, vibration, current, shift)
        
        # Return in legacy format
        return {
            "temperature": temperature,
            "vibration": vibration,
            "load": load,
            "shift": shift,
            "downtime_probability": result['downtime_probability'],
            "downtime_predicted": result['downtime_predicted'],
            "risk_level": result['risk_level']
        }
        
    except Exception as e:
        logger.error(f"Legacy prediction API error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
