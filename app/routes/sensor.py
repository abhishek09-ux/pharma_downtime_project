# app/routes/sensor.py (excerpt)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.downtime import Downtime
from app.ml.model import predict_downtime  # your predict function
from app.core.ws_manager import ws_manager
from datetime import datetime

router = APIRouter()

@router.post("/sensor-data/")
async def receive_sensor_data(
    machine_id: str,
    machine_temperature: float,
    vibration_level: float,
    humidity: float,
    shift_time: int,
    db: Session = Depends(get_db)
):
    # Only pass the features your model expects
    probability = predict_downtime(machine_temperature, vibration_level, humidity, shift_time)  # returns 0 or 1

    # Save to DB
    event = Downtime(
        machine_id=machine_id,
        reason="sensor_reading",
        duration_minutes=0.0,
        timestamp=datetime.utcnow(),
        # optionally include sensor fields in your model or use metadata table
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Build broadcast payload
    payload = {
        "type": "sensor_update",
        "machine_id": machine_id,
        "temperature": machine_temperature,
        "vibration": vibration_level,
        "humidity": humidity,
        "shift": shift_time,
        "downtime_probability": round(float(probability), 3),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Broadcast to all connected websocket clients
    await ws_manager.broadcast(payload)

    return {"status": "success", "downtime_probability": probability}
