# app/routes/downtime_routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/downtime", tags=["Downtime"])

@router.get("/test")
def test():
    return {"status": "Downtime route working!"}
# app/routes/downtime_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.downtime_schema import DowntimeCreate, DowntimeResponse
from app.services.downtime_service import create_downtime, get_all_downtimes, get_downtime_prediction
from typing import List

router = APIRouter(prefix="/downtime", tags=["Downtime"])

@router.post("/", response_model=DowntimeResponse)
def log_downtime(downtime: DowntimeCreate, db: Session = Depends(get_db)):
    return create_downtime(db, downtime)

@router.get("/", response_model=List[DowntimeResponse])
def fetch_downtimes(db: Session = Depends(get_db)):
    return get_all_downtimes(db)

@router.get("/predict/{machine_id}")
def predict_downtime(machine_id: str):
    return get_downtime_prediction(machine_id)

from fastapi import Query

@router.get("/predict/{machine_id}")
def predict_downtime(
    machine_id: int,
    avg_temp: float = Query(..., description="Average machine temperature"),
    avg_vibration: float = Query(..., description="Average machine vibration level"),
    past_failures: int = Query(..., description="Number of past failures")
):
    return get_downtime_prediction(machine_id, avg_temp, avg_vibration, past_failures)
