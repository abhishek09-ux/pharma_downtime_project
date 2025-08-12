from pydantic import BaseModel
from datetime import datetime

# Schema for creating downtime entry
class DowntimeCreate(BaseModel):
    machine_id: str
    reason: str
    duration_minutes: float

# Schema for returning downtime data
class DowntimeResponse(DowntimeCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # Allows ORM objects to work with Pydantic v2
