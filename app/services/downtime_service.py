from sqlalchemy.orm import Session
from app.models.downtime import Downtime
from app.schemas.downtime_schema import DowntimeCreate

def create_downtime(db: Session, downtime_data: DowntimeCreate):
    new_downtime = Downtime(**downtime_data.dict())
    db.add(new_downtime)
    db.commit()
    db.refresh(new_downtime)
    return new_downtime

def get_all_downtimes(db: Session):
    return db.query(Downtime).all()

from app.utils.ml_model import predict_downtime_risk

def get_downtime_prediction(machine_id: str):
    return predict_downtime_risk(machine_id)
def get_downtime_prediction(machine_id: int, avg_temp: float, avg_vibration: float, past_failures: int):
    from app.utils.ml_model import predict_downtime_risk
    return predict_downtime_risk(machine_id, avg_temp, avg_vibration, past_failures)
