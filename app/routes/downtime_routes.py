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

from fastapi import Query

@router.get("/predict/{machine_id}")
def predict_downtime(
    machine_id: str,
    avg_temp: float = Query(..., description="Average machine temperature"),
    avg_vibration: float = Query(..., description="Average machine vibration level"),
    past_failures: int = Query(..., description="Number of past failures")
):
    return get_downtime_prediction(machine_id, avg_temp, avg_vibration, past_failures)

from app.utils.report_generator import generate_downtime_report

@router.get("/report")
def downtime_report(db: Session = Depends(get_db)):
    return generate_downtime_report(db)

from app.utils.pdf_generator import generate_downtime_pdf
from app.utils.email_sender import send_email_with_pdf
import tempfile
import os

from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
import io

@router.post("/pdf-or-send-report")
async def pdf_or_send_report(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        data = {}
    receiver_email = data.get("receiver_email") if isinstance(data, dict) else None
    pdf_bytes = generate_downtime_pdf(db)
    if pdf_bytes is None:
        return JSONResponse(content={"error": "No downtime events to generate PDF"}, status_code=404)
    if receiver_email:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(temp_file.name, "wb") as f:
            f.write(pdf_bytes)
        result = send_email_with_pdf(receiver_email, temp_file.name)
        os.remove(temp_file.name)
        return JSONResponse(content={"status": "sent", "detail": result})
    else:
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=downtime_report.pdf"})
