import csv
from typing import List, Set, Dict, Any, Optional, Union, Callable

import matplotlib
matplotlib.use('Agg')  # Headless backend for server environments

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.container import BarContainer

import io
import base64
import asyncio
import numpy as np
import joblib

from fastapi import FastAPI, Depends, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Database availability flag
database_available: bool = False
routes_available: bool = False

# Initialize database-related variables with proper types
Base: Optional[Any] = None
engine: Optional[Any] = None
get_db: Optional[Callable[[], Session]] = None
Downtime: Optional[Any] = None
downtime_routes: Optional[Any] = None
sensor: Optional[Any] = None

# Try importing database modules
try:
    from app.core.database import Base, engine, get_db
    from app.models.downtime import Downtime
    database_available = True
except ImportError:
    pass

# Try importing route modules
try:
    from app.routes import downtime_routes, sensor
    routes_available = True
except ImportError:
    pass

# Create all tables only if database is available
if database_available and Base is not None and engine is not None:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pharma Downtime Project", version="1.0")

# Endpoint: Serve CSV as JSON
@app.get("/csv-data")
def get_csv_data() -> Dict[str, Any]:
    data: List[Dict[str, Any]] = []
    try:
        with open("downtime_data.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row["temperature"] = float(row["temperature"])
                row["vibration"] = float(row["vibration"])
                row["machine_load"] = float(row["machine_load"])
                row["shift"] = int(row["shift"])
                row["downtime_occurred"] = int(row["downtime_occurred"])
                data.append(row)
    except FileNotFoundError:
        return {"data": [], "error": "CSV file not found"}
    except Exception as e:
        return {"data": [], "error": str(e)}
    return {"data": data}

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: Generate chart image
def generate_chart(events: List[Any]) -> bytes:
    machine_ids: List[Union[str, int]] = [getattr(e, 'machine_id', '') for e in events]
    durations: List[Union[float, int]] = [getattr(e, 'duration_minutes', 0) for e in events]
    
    figure: Figure
    ax: Axes
    figure, ax = plt.subplots(figsize=(8, 4))
    
    bar_container: BarContainer = ax.bar(machine_ids, durations, color='skyblue')
    if len(bar_container) > 0:  # Safer check for bar container
        bar_container[0].set_color('lightblue')
    
    ax.set_xlabel('Machine ID')
    ax.set_ylabel('Downtime Duration (minutes)')
    ax.set_title('Downtime Duration by Machine')
    figure.tight_layout()
    
    buf: io.BytesIO = io.BytesIO()
    figure.savefig(buf, format='png')
    buf.seek(0)
    img_bytes: bytes = buf.read()
    plt.close(figure)
    return img_bytes

# Endpoint: HTML report
@app.get("/report")
def get_report(db: Optional[Session] = Depends(get_db) if database_available and get_db is not None else None) -> Response:
    if not database_available or db is None or Downtime is None:
        content: str = "<h2>Database not available.</h2>"
        return Response(content=content, media_type="text/html")
    
    events: List[Any] = db.query(Downtime).all()
    if not events:
        no_events_content: str = "<h2>No downtime events found.</h2>"
        return Response(content=no_events_content, media_type="text/html")

    total_events: int = len(events)
    avg_duration: float = round(sum(getattr(e, 'duration_minutes', 0) for e in events) / total_events, 2)
    img_bytes: bytes = generate_chart(events)
    img_base64: str = base64.b64encode(img_bytes).decode('utf-8')

    html: str = f"""
    <html>
    <head><title>Downtime Report</title></head>
    <body>
        <h1>Downtime Report</h1>
        <p>Total Events: {total_events}</p>
        <p>Average Duration: {avg_duration} min</p>
        <img src="data:image/png;base64,{img_base64}" alt="Downtime Chart" />
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

# Endpoint: Chart only
@app.get("/report/chart")
def get_report_chart(db: Optional[Session] = Depends(get_db) if database_available and get_db is not None else None) -> Response:
    if not database_available or db is None or Downtime is None:
        error_content: str = "Database not available."
        return Response(content=error_content, media_type="text/plain")
    
    events: List[Any] = db.query(Downtime).all()
    if not events:
        no_chart_content: str = "No chart available."
        return Response(content=no_chart_content, media_type="text/plain")
    
    img_bytes: bytes = generate_chart(events)
    return Response(content=img_bytes, media_type="image/png")

# Endpoint: Prediction
@app.get("/predict")
def predict_endpoint(temperature: float, vibration: float, load: float, shift: int) -> Dict[str, Any]:
    try:
        model: Any = joblib.load("app/ml/downtime_model.pkl")
        features: List[Union[float, int]] = [temperature, vibration, load, shift]
        feature_array: np.ndarray = np.array(features).reshape(1, -1)
        
        if hasattr(model, 'predict_proba'):
            prob_result: np.ndarray = model.predict_proba(feature_array)
            prob: float = float(prob_result[0][1])
            pred_result: np.ndarray = model.predict(feature_array)
            pred: Any = pred_result[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_probability": round(prob, 2),
                "downtime_predicted": bool(pred)
            }
        else:
            pred_array: np.ndarray = model.predict(feature_array)
            pred_final: Any = pred_array[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_predicted": bool(pred_final)
            }
    except Exception as e:
        error_dict: Dict[str, str] = {"error": str(e)}
        return error_dict

# Include routers if available
if routes_available and downtime_routes is not None and hasattr(downtime_routes, 'router'):
    app.include_router(downtime_routes.router)
if routes_available and sensor is not None and hasattr(sensor, 'router'):
    app.include_router(sensor.router)

# Root endpoint
@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Welcome to the Pharma Downtime API! All endpoints are available at /docs."}

# WebSocket clients
clients: Set[WebSocket] = set()

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket) -> None:
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # Keep-alive ping
    except Exception:
        pass
    finally:
        clients.discard(websocket)
