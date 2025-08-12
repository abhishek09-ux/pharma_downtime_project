from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.downtime import Downtime
from app.schemas.downtime_schema import DowntimeCreate, DowntimeResponse

router = APIRouter()

@router.post("/downtime/", response_model=DowntimeResponse)
def create_downtime_event(event: DowntimeCreate, db: Session = Depends(get_db)):
    new_event = Downtime(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.get("/downtime/", response_model=list[DowntimeResponse])
def get_all_downtime_events(db: Session = Depends(get_db)):
    return db.query(Downtime).all()

@router.get("/downtime/{event_id}", response_model=DowntimeResponse)
def get_downtime_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Downtime).filter(Downtime.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

## Removed duplicate and incorrect DowntimeEvent references. Use only DowntimeCreate, DowntimeResponse, and Downtime ORM model as above.
