import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from app.models.downtime import Downtime
import io
from fastapi.responses import StreamingResponse

def generate_downtime_report(db: Session):
    # Fetch all downtime events
    events = db.query(Downtime).all()

    if not events:
        return {"error": "No downtime events to generate report"}

    # Prepare data
    machine_ids = [event.machine_id for event in events]
    durations = [event.duration_minutes for event in events]

    # Create plot
    plt.figure(figsize=(8, 5))
    plt.bar(machine_ids, durations, color="skyblue")
    plt.xlabel("Machine ID")
    plt.ylabel("Downtime (minutes)")
    plt.title("Downtime Duration per Machine")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save plot to in-memory file
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close()

    return StreamingResponse(img_io, media_type="image/png")
