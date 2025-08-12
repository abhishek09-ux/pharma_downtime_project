from sqlalchemy import Column, Integer, String, DateTime, Float
from app.core.database import Base
from datetime import datetime

class Downtime(Base):
    __tablename__ = "downtime_events"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)  # Machine identifier
    reason = Column(String)  # Reason for downtime
    duration_minutes = Column(Float)  # Duration in minutes
    timestamp = Column(DateTime, default=datetime.utcnow)  # Event time
