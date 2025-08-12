
# main.py
from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from app.core.database import Base, engine, get_db
from app.models.downtime import Downtime
from app.routes import downtime_routes, sensor
from app.ml.model import predict_downtime

# Create all tables
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Pharma Downtime Project", version="1.0")
app.include_router(downtime_routes.router)
app.include_router(sensor.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Pharma Downtime API! All endpoints are available at /docs."}

# Helper function to generate chart image
def generate_chart(events):
    machine_ids = [e.machine_id for e in events]
    durations = [e.duration_minutes for e in events]
    plt.figure(figsize=(8, 4))
    plt.bar(machine_ids, durations, color='skyblue')
    plt.xlabel('Machine ID')
    plt.ylabel('Downtime Duration (minutes)')
    plt.title('Downtime Duration by Machine')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_bytes = buf.read()
    plt.close()
    return img_bytes

@app.get("/report")
def get_report(db: Session = Depends(get_db)):
    events = db.query(Downtime).all()
    if not events:
        html = """
        <html><head><title>Downtime Report</title></head><body>
        <h2>No downtime events found.</h2>
        </body></html>
        """
        return Response(content=html, media_type="text/html")

    total_events = len(events)
    avg_duration = round(sum([e.duration_minutes for e in events]) / total_events, 2)
    img_bytes = generate_chart(events)
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    html = f"""
    <html>
    <head>
        <title>Downtime Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }}
            .container {{ max-width: 800px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 32px; }}
            h1 {{ color: #2a3f5f; }}
            .summary {{ display: flex; gap: 32px; margin-bottom: 32px; }}
            .summary div {{ background: #eaf1fb; border-radius: 8px; padding: 16px 24px; font-size: 1.2em; color: #2a3f5f; box-shadow: 0 1px 4px #0001; }}
            .chart {{ text-align: center; }}
            img {{ border-radius: 8px; box-shadow: 0 1px 8px #0002; margin-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Downtime Report</h1>
            <div class="summary">
                <div><strong>Total Events:</strong> {total_events}</div>
                <div><strong>Average Duration:</strong> {avg_duration} min</div>
            </div>
            <div class="chart">
                <h2>Downtime Duration by Machine</h2>
                <img src="data:image/png;base64,{img_base64}" alt="Downtime Chart" width="600" />
            </div>
        </div>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

@app.get("/report/chart")
def get_report_chart(db: Session = Depends(get_db)):
    events = db.query(Downtime).all()
    if not events:
        return Response(content="No chart available.", media_type="text/plain")
    img_bytes = generate_chart(events)
    return Response(content=img_bytes, media_type="image/png")

@app.get("/predict")
def predict_endpoint(temperature: float, vibration: float, load: float, shift: int):
    import joblib
    import numpy as np
    try:
        # Load model trained with 4 features
        model = joblib.load("app/ml/downtime_model.pkl")
        features = [temperature, vibration, load, shift]
        if hasattr(model, 'predict_proba'):
            prob = model.predict_proba(np.array(features).reshape(1, -1))[0][1]
            pred = model.predict(np.array(features).reshape(1, -1))[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_probability": round(prob, 2),
                "downtime_predicted": bool(pred)
            }
        else:
            pred = model.predict(np.array(features).reshape(1, -1))[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_predicted": bool(pred)
            }
    except Exception as e:
        return {"error": str(e)}


# Remove duplicate app creation and router includes
# All routers should be included in the main app instance above
# If you want to include additional routers, do it after the main app is created:
# app.include_router(sensor.router)
# app.include_router(ws_routes.router)
