from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.models.downtime import Downtime
import io
from fastapi.responses import StreamingResponse
from datetime import datetime

def generate_downtime_pdf(db: Session):
    events = db.query(Downtime).all()

    if not events:
        return None

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Downtime Report")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 730, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Table Header
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Machine ID")
    pdf.drawString(150, 700, "Reason")
    pdf.drawString(300, 700, "Duration (min)")
    pdf.drawString(420, 700, "Timestamp")

    y = 680
    pdf.setFont("Helvetica", 10)

    for event in events:
        pdf.drawString(50, y, str(event.machine_id))
        pdf.drawString(150, y, event.reason)
        pdf.drawString(300, y, str(event.duration_minutes))
        pdf.drawString(420, y, event.timestamp.strftime("%Y-%m-%d %H:%M"))
        y -= 20
        if y < 50:  # New page if needed
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
