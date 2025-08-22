import csv
from typing import List, Set, Dict, Any
import datetime
import random
import asyncio
import numpy as np
import pickle
import json
import logging
import platform
import sys
import os

# Set up logger
logger = logging.getLogger("pharma_downtime")
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Pharma Downtime Project", version="1.0")

# Mount pharma-dashboard files
app.mount("/static", StaticFiles(directory="pharma-dashboard"), name="static")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint: Serve CSV as JSON
@app.get("/csv-data")
def get_csv_data() -> Dict[str, Any]:
    data = []
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

# Endpoint: Prediction
@app.get("/predict")
def predict_endpoint(temperature: float, vibration: float, load: float, shift: int) -> Dict[str, Any]:
    try:
        with open("app/ml/downtime_model.pkl", "rb") as f:
            model = pickle.load(f)
        features = [temperature, vibration, load, shift]
        feature_array = np.array(features).reshape(1, -1)
        
        if hasattr(model, 'predict_proba'):
            prob_result = model.predict_proba(feature_array)
            prob = float(prob_result[0][1])
            pred_result = model.predict(feature_array)
            pred = pred_result[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_probability": round(prob, 2),
                "downtime_predicted": bool(pred)
            }
        else:
            pred_array = model.predict(feature_array)
            pred_final = pred_array[0]
            return {
                "temperature": temperature,
                "vibration": vibration,
                "load": load,
                "shift": shift,
                "downtime_predicted": bool(pred_final)
            }
    except Exception as e:
        return {"error": str(e)}

# Dashboard data endpoints
@app.get("/api/dashboard/stats")
def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics"""
    return {
        "total_downtimes": random.randint(60, 70),
        "avg_risk": round(random.uniform(0.5, 0.6), 2),
        "machines_online": 3,
        "machines_offline": 7
    }

@app.get("/api/dashboard/events")
def get_recent_events() -> Dict[str, Any]:
    """Get recent machine events"""
    events = []
    machine_names = ["Machine1", "Machine2", "Machine3"]
    
    for _ in range(random.randint(10, 15)):
        event_time = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 300))
        temp = round(random.uniform(60, 95), 1)
        vib = round(random.uniform(1.5, 5.0), 1)
        risk_percent = round(random.uniform(10, 90), 1)
        
        if temp > 85 or vib > 4.0:
            status = "CRITICAL"
        elif temp > 75 or vib > 3.0:
            status = "WARNING"
        else:
            status = "OK"
        
        events.append({
            "time": event_time.strftime("%I:%M %p"),
            "machine": random.choice(machine_names),
            "temp": temp,
            "vib": vib,
            "risk": f"{risk_percent}%",
            "status": status
        })
    
    return {"events": events}

@app.get("/api/dashboard/machines")
def get_machine_list() -> Dict[str, Any]:
    """Get list of machines for dropdown"""
    machines = [
        {"id": "Machine1", "name": "Machine1"},
        {"id": "Machine2", "name": "Machine2"},
        {"id": "Machine3", "name": "Machine3"}
    ]
    return {"machines": machines}

@app.get("/api/dashboard/chart/{machine_id}")
def get_machine_chart_data(machine_id: str) -> Dict[str, Any]:
    """Get chart data for specific machine"""
    timestamps = []
    risk_values = []
    base_time = datetime.datetime.now() - datetime.timedelta(hours=2)
    
    for i in range(120):
        timestamp = base_time + datetime.timedelta(minutes=i)
        timestamps.append(timestamp.strftime("%I:%M %p"))
        
        if i < 30:
            risk = round(random.uniform(0.6, 0.9), 2)
        elif i < 60:
            risk = round(random.uniform(0.4, 0.7), 2)
        elif i < 90:
            risk = round(random.uniform(0.7, 1.0), 2)
        else:
            risk = round(random.uniform(0.3, 0.6), 2)
            
        risk_values.append(risk)
    
    return {
        "machine_id": machine_id,
        "timestamps": timestamps,
        "risk": risk_values
    }

@app.get("/api/generate-sample-data")
def generate_sample_data() -> Dict[str, Any]:
    """Generate sample data for testing"""
    sample_data = []
    machine_ids = ["Machine1", "Machine2", "Machine3"]
    
    for _ in range(100):
        temp = round(random.uniform(65, 95), 1)
        vib = round(random.uniform(1.0, 5.0), 1)
        load = round(random.uniform(70, 100), 1)
        shift = random.randint(1, 3)
        downtime = 1 if (temp > 85 or vib > 4.0 or load > 95) else 0
        
        sample_data.append({
            "machine_id": random.choice(machine_ids),
            "temperature": temp,
            "vibration": vib,
            "machine_load": load,
            "shift": shift,
            "downtime_occurred": downtime
        })
    
    try:
        with open("downtime_data.csv", "w", newline="") as csvfile:
            fieldnames = ["machine_id", "temperature", "vibration", "machine_load", "shift", "downtime_occurred"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_data)
        return {"message": f"Generated {len(sample_data)} sample records", "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

# Advanced Analytics endpoint
@app.get("/api/advanced-analytics")
def get_advanced_analytics() -> Dict[str, Any]:
    """Get advanced analytics data including ML predictions and trends"""
    # Generate historical efficiency data
    historical_data = []
    for i in range(30):
        date = datetime.datetime.now() - datetime.timedelta(days=i)
        efficiency = round(random.uniform(75, 95), 1)
        downtimes = random.randint(0, 5)
        historical_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "efficiency": efficiency,
            "downtimes": downtimes
        })
    
    # Generate predictions
    predictions = []
    for i in range(1, 8):
        future_date = datetime.datetime.now() + datetime.timedelta(days=i)
        risk_score = round(random.uniform(0.2, 0.8), 2)
        predicted_efficiency = round(random.uniform(80, 95), 1)
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "risk_score": risk_score,
            "predicted_efficiency": predicted_efficiency
        })
    
    return {
        "historical_trends": historical_data,
        "ml_predictions": predictions,
        "model_accuracy": round(random.uniform(87, 94), 1),
        "insights": {
            "top_risk_factors": ["High Temperature", "Excessive Vibration", "Overload"],
            "recommended_actions": ["Schedule maintenance for Machine2", "Check cooling system"],
            "efficiency_trend": "improving"
        },
        "last_updated": datetime.datetime.now().isoformat()
    }

# Admin operations
@app.get("/api/admin/settings")
def get_admin_settings() -> Dict[str, Any]:
    """Get admin dashboard settings"""
    return {
        "alert_thresholds": {"temperature": 85.0, "vibration": 4.0, "risk": 0.8},
        "notification_settings": {"email_alerts": True, "sms_alerts": False, "dashboard_alerts": True},
        "system_info": {"version": "1.0", "uptime": "72h 34m", "last_backup": "2024-01-15 10:30:00"},
        "users": [
            {"id": 1, "name": "Admin User", "role": "administrator", "last_login": "2024-01-15 14:30:00"},
            {"id": 2, "name": "Operator", "role": "operator", "last_login": "2024-01-15 13:45:00"}
        ]
    }

@app.post("/api/admin/add-machine")
def add_machine() -> Dict[str, Any]:
    """Add new machine to monitoring system"""
    new_machine_id = f"Machine{random.randint(4, 10)}"
    return {
        "success": True,
        "message": f"Machine {new_machine_id} added successfully",
        "machine_id": new_machine_id,
        "initial_status": "Online",
        "initial_risk": round(random.uniform(0.1, 0.3), 2)
    }

# Hardware sensor endpoints
@app.post("/api/hardware/sensor-data")
async def receive_sensor_data(sensor_data: dict) -> Dict[str, Any]:
    """Receive real-time sensor data from Raspberry Pi"""
    try:
        # Store sensor data (you can add database storage here)
        logger.info(f"Received sensor data from {sensor_data.get('machine_id')}")
        
        # Broadcast to connected WebSocket clients
        if clients:
            message = {
                "type": "sensor_update",
                **sensor_data
            }
            disconnected_clients = set()
            for client in clients:
                try:
                    await client.send_text(json.dumps(message))
                except:
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            clients -= disconnected_clients
        
        return {"status": "success", "message": "Sensor data received"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/hardware/machines")
def get_hardware_machines() -> Dict[str, Any]:
    """Get list of connected hardware machines"""
    # In production, this would query a database of registered devices
    return {
        "machines": [
            {
                "id": "Machine1",
                "name": "Tablet Press 1", 
                "location": "Production Floor A",
                "status": "online",
                "last_seen": datetime.datetime.now().isoformat(),
                "sensors": ["MLX90614", "DHT22", "ADXL335"]
            },
            {
                "id": "Machine2", 
                "name": "Mixer Unit 1",
                "location": "Production Floor B", 
                "status": "online",
                "last_seen": datetime.datetime.now().isoformat(),
                "sensors": ["MLX90614", "DHT22", "ADXL335"]
            }
        ]
    }

@app.get("/api/hardware/status/{machine_id}")
def get_machine_status(machine_id: str) -> Dict[str, Any]:
    """Get detailed status of specific hardware machine"""
    return {
        "machine_id": machine_id,
        "status": "online",
        "uptime": "72h 15m",
        "sensor_health": {
            "MLX90614": "healthy",
            "DHT22": "healthy", 
            "ADXL335": "healthy"
        },
        "last_readings": {
            "temperature": round(random.uniform(20, 30), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "vibration": round(random.uniform(1.0, 3.0), 3)
        },
        "wifi_signal": random.randint(-70, -30),
        "battery_level": random.randint(75, 100)
    }

# Add a new endpoint for environment status
@app.get("/api/system/environment")
def get_environment_status() -> Dict[str, Any]:
    """Get system environment status"""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "virtual_env": sys.prefix != sys.base_prefix,
        "working_directory": os.getcwd(),
        "python_executable": sys.executable
    }

# Root endpoint - serve your pharma-dashboard index.html
@app.get("/")
def root() -> Response:
    try:
        # Try to serve React build first, then fall back to HTML
        try:
            with open("pharma-dashboard/build/index.html", "r", encoding="utf-8") as file:
                html_content = file.read()
            return Response(content=html_content, media_type="text/html")
        except FileNotFoundError:
            # Fall back to standalone HTML dashboard
            with open("pharma-dashboard/index.html", "r", encoding="utf-8") as file:
                html_content = file.read()
            return Response(content=html_content, media_type="text/html")
    except FileNotFoundError:
        return Response(
            content="<h1>Dashboard not found</h1><p>Please make sure your pharma-dashboard folder contains index.html or build the React app</p>", 
            media_type="text/html"
        )

# Serve React static files if they exist
@app.get("/static/js/{filename}")
async def serve_react_js(filename: str):
    try:
        with open(f"pharma-dashboard/build/static/js/{filename}", "rb") as file:
            content = file.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        return Response(status_code=404)

@app.get("/static/css/{filename}")
async def serve_react_css(filename: str):
    try:
        with open(f"pharma-dashboard/build/static/css/{filename}", "rb") as file:
            content = file.read()
        return Response(content=content, media_type="text/css")
    except FileNotFoundError:
        return Response(status_code=404)

# WebSocket for real-time monitoring
clients: Set[WebSocket] = set()

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket) -> None:
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(10)
    except Exception:
        pass
    finally:
        clients.discard(websocket)
