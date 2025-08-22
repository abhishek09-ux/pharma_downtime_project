import csv
from typing import List, Set, Dict, Any
from datetime import datetime
import random
import asyncio
import json
import logging

# Set up logger
logger = logging.getLogger("pharma_downtime")
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI(title="Pharma Downtime Monitoring System")

# List to keep track of connected WebSocket clients
connected_websockets = []

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for sensor data
sensor_data = {
    "temperature": {"value": 25.4, "status": "online", "unit": "°C"},
    "vibration": {"value": 3.2, "status": "online", "unit": "Hz"},
    "pressure": {"value": 15.8, "status": "online", "unit": "PSI"},
    "current": {"value": 2.1, "status": "online", "unit": "A"}
}

events_log = []

# Try to import Raspberry Pi libraries
try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
    logger.info("✅ Raspberry Pi libraries loaded - REAL SENSOR MODE")
except ImportError:
    RASPBERRY_PI = False
    logger.info("⚠️ Running in SIMULATION MODE - Raspberry Pi libraries not found")

class SensorManager:
    def __init__(self):
        self.running = False
        self.mode = "REAL SENSORS" if RASPBERRY_PI else "SIMULATION"
        logger.info(f"🚀 SensorManager initialized in {self.mode} mode")
        
    async def read_sensors(self):
        """Read data from all sensors"""
        global sensor_data
        
        if RASPBERRY_PI:
            # REAL SENSOR MODE - would read from actual hardware
            pass
        else:
            # SIMULATION MODE - Generate realistic pharmaceutical sensor data
            sensor_data["temperature"]["value"] = round(20 + random.uniform(0, 40), 1)
            sensor_data["temperature"]["status"] = "online"
            
            sensor_data["vibration"]["value"] = round(random.uniform(0, 10), 2)
            sensor_data["vibration"]["status"] = "online"
            
            sensor_data["pressure"]["value"] = round(10 + random.uniform(0, 20), 1)
            sensor_data["pressure"]["status"] = "online"
            
            sensor_data["current"]["value"] = round(1 + random.uniform(0, 5), 2)
            sensor_data["current"]["status"] = "online"
    
    async def log_event(self):
        """Log sensor readings as events"""
        global events_log
        
        now = datetime.now()
        temp = sensor_data["temperature"]["value"]
        vib = sensor_data["vibration"]["value"]
        risk = random.uniform(30, 90)
        
        # Determine status based on thresholds
        status = "OK"
        if temp > 50 or vib > 5:
            status = "WARNING"
        if temp > 70 or vib > 8:
            status = "CRITICAL"
        
        machine_prefix = "REAL-" if RASPBERRY_PI else "SIM-"
        
        event = {
            "time": now.strftime("%I:%M %p"),
            "machine": f"{machine_prefix}Machine{random.randint(1, 3)}",
            "temp": f"{temp}°C",
            "vib": str(vib),
            "risk": f"{risk:.1f}%",
            "status": status,
            "timestamp": now.isoformat(),
            "mode": self.mode
        }
        
        events_log.insert(0, event)
        events_log = events_log[:50]
    
    async def start_monitoring(self):
        """Start continuous sensor monitoring"""
        self.running = True
        logger.info(f"🔄 Starting sensor monitoring in {self.mode} mode...")
        
        while self.running:
            await self.read_sensors()
            await self.log_event()
            await asyncio.sleep(5)

sensor_manager = SensorManager()

# Clean HTML Dashboard
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pharma Downtime Monitoring Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; min-height: 100vh; }
        .sidebar { position: fixed; left: 0; top: 0; width: 80px; height: 100vh; background: #2563eb; display: flex; flex-direction: column; align-items: center; padding: 20px 0; z-index: 1000; }
        .sidebar-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.1); border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; cursor: pointer; transition: all 0.3s ease; color: white; font-size: 20px; }
        .sidebar-icon:hover { background: rgba(255,255,255,0.2); }
        .sidebar-icon.active { background: rgba(255,255,255,0.3); }
        .main-content { margin-left: 80px; padding: 0; }
        .header { background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header-left { display: flex; align-items: center; gap: 15px; }
        .logo-text { color: #2563eb; font-size: 1.5rem; font-weight: bold; }
        .status-badge { padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; background: #10b981; color: white; }
        .mode-badge { padding: 6px 12px; border-radius: 15px; font-size: 0.8rem; margin-left: 10px; background: #f59e0b; color: white; }
        .dashboard-content { padding: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #2563eb; }
        .metric-header { color: #6b7280; font-size: 0.9rem; margin-bottom: 10px; }
        .metric-value { display: flex; align-items: center; gap: 10px; font-size: 2rem; font-weight: bold; color: #1f2937; }
        .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .chart-section, .events-section { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .events-table { width: 100%; border-collapse: collapse; }
        .events-table th { background: #f8fafc; padding: 15px; text-align: left; color: #6b7280; font-weight: 600; border-bottom: 2px solid #e5e7eb; }
        .events-table td { padding: 15px; border-bottom: 1px solid #e5e7eb; color: #1f2937; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; transition: all 0.3s ease; }
        .filter-buttons { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .filter-btn { padding: 8px 16px; border: 2px solid; border-radius: 20px; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: all 0.3s ease; background: white; }
        .filter-btn.active { color: white !important; }
        .filter-btn.all { border-color: #2563eb; color: #2563eb; }
        .filter-btn.all.active { background: #2563eb; }
        .filter-btn.critical { border-color: #ef4444; color: #ef4444; }
        .filter-btn.critical.active { background: #ef4444; }
        .filter-btn.warning { border-color: #f59e0b; color: #f59e0b; }
        .filter-btn.warning.active { background: #f59e0b; }
        .filter-btn.ok { border-color: #10b981; color: #10b981; }
        .filter-btn.ok.active { background: #10b981; }
        .status-icon { display: inline-flex; align-items: center; gap: 5px; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        .status-critical { background: #fee2e2; color: #dc2626; }
        .status-warning { background: #fef3c7; color: #92400e; }
        .status-ok { background: #dcfce7; color: #166534; }
        .toast { position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 15px 20px; border-radius: 8px; z-index: 3000; transform: translateX(400px); transition: transform 0.3s ease; }
        .toast.show { transform: translateX(0); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-icon active" title="Dashboard" onclick="showSection('dashboard')">📊</div>
        <div class="sidebar-icon" title="Machines" onclick="showSection('machines')">⚙️</div>
        <div class="sidebar-icon" title="Settings" onclick="showSection('settings')">⚙️</div>
        <div class="sidebar-icon" title="Notifications" onclick="showSection('notifications')">🔔</div>
    </div>

    <div class="main-content">
        <header class="header">
            <div class="header-left">
                <div class="logo-text">📊 Pharma Downtime Monitoring</div>
                <div class="status-badge">Live</div>
                <div class="mode-badge">🎭 SIMULATION</div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button class="btn" style="background: #2563eb; color: white;" onclick="showToast('Add Machine modal opened!')">Add Machine</button>
                <button class="btn" style="background: #1e40af; color: white;" onclick="showToast('Admin panel accessed!')">Admin</button>
                <div style="background: #2563eb; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;" onclick="showToast('User profile opened!')">👤</div>
            </div>
        </header>

        <div class="dashboard-content" id="dashboard-section">
            <div class="metrics-grid">
                <div class="metric-card" style="border-left-color: #ef4444;">
                    <div class="metric-header">Temperature</div>
                    <div class="metric-value">
                        <span style="color: #ef4444;">🌡️</span>
                        <span id="temp-value">25.4°C</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #f59e0b;">
                    <div class="metric-header">Vibration</div>
                    <div class="metric-value">
                        <span style="color: #f59e0b;">📳</span>
                        <span id="vib-value">3.2 Hz</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #10b981;">
                    <div class="metric-header">Pressure</div>
                    <div class="metric-value">
                        <span style="color: #10b981;">📏</span>
                        <span id="pressure-value">15.8 PSI</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #2563eb;">
                    <div class="metric-header">Current</div>
                    <div class="metric-value">
                        <span style="color: #2563eb;">⚡</span>
                        <span id="current-value">2.1 A</span>
                    </div>
                </div>
            </div>

            <div class="content-grid">
                <div class="chart-section">
                    <h3>📈 Live Sensor Data</h3>
                    <div style="margin: 20px 0;">
                        <div>Temperature: <span style="color: #10b981; font-weight: bold;">Online</span></div>
                        <div>Vibration: <span style="color: #10b981; font-weight: bold;">Online</span></div>
                        <div>Pressure: <span style="color: #10b981; font-weight: bold;">Online</span></div>
                        <div>Current: <span style="color: #10b981; font-weight: bold;">Online</span></div>
                        <div style="margin-top: 15px; padding: 10px; background: #f8fafc; border-radius: 8px;">
                            <strong>Mode:</strong> SIMULATION
                        </div>
                    </div>
                </div>

                <div class="events-section">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3>📊 Recent Events</h3>
                        <button class="btn" style="background: #10b981; color: white; font-size: 0.9rem;" onclick="exportEvents()">⬇️ Export</button>
                    </div>
                    
                    <div class="filter-buttons">
                        <button class="filter-btn all active" onclick="filterEvents('all')">🔵 ALL</button>
                        <button class="filter-btn critical" onclick="filterEvents('critical')">🔴 CRITICAL</button>
                        <button class="filter-btn warning" onclick="filterEvents('warning')">🟡 WARNING</button>
                        <button class="filter-btn ok" onclick="filterEvents('ok')">🟢 OK</button>
                    </div>
                    
                    <table class="events-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Machine</th>
                                <th>Temp</th>
                                <th>Vib</th>
                                <th>Risk</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="events-tbody">
                            <tr>
                                <td>02:15 PM</td>
                                <td>SIM-Machine1</td>
                                <td>35.2°C</td>
                                <td>4.1</td>
                                <td>45.8%</td>
                                <td><span class="status-icon status-ok">🟢 OK</span></td>
                            </tr>
                            <tr>
                                <td>02:10 PM</td>
                                <td>SIM-Machine2</td>
                                <td>58.7°C</td>
                                <td>6.3</td>
                                <td>72.4%</td>
                                <td><span class="status-icon status-warning">🟡 WARNING</span></td>
                            </tr>
                            <tr>
                                <td>02:05 PM</td>
                                <td>SIM-Machine3</td>
                                <td>75.1°C</td>
                                <td>8.9</td>
                                <td>89.2%</td>
                                <td><span class="status-icon status-critical">🔴 CRITICAL</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="dashboard-content" id="machines-section" style="display: none;">
            <h2>🔧 Machine Management</h2>
            <p>Machine configuration and status management.</p>
        </div>

        <div class="dashboard-content" id="settings-section" style="display: none;">
            <h2>⚙️ System Settings</h2>
            <p>System configuration options.</p>
        </div>

        <div class="dashboard-content" id="notifications-section" style="display: none;">
            <h2>🔔 Notifications</h2>
            <p>Alert and notification management.</p>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let currentFilter = 'all';
        let allEvents = [
            {time: "02:15 PM", machine: "SIM-Machine1", temp: "35.2°C", vib: "4.1", risk: "45.8%", status: "OK"},
            {time: "02:10 PM", machine: "SIM-Machine2", temp: "58.7°C", vib: "6.3", risk: "72.4%", status: "WARNING"},
            {time: "02:05 PM", machine: "SIM-Machine3", temp: "75.1°C", vib: "8.9", risk: "89.2%", status: "CRITICAL"}
        ];
        
        function updateSensorValues() {
            const temp = (20 + Math.random() * 40).toFixed(1);
            const vib = (Math.random() * 10).toFixed(1);
            const pressure = (10 + Math.random() * 20).toFixed(1);
            const current = (1 + Math.random() * 5).toFixed(1);
            
            document.getElementById('temp-value').textContent = temp + '°C';
            document.getElementById('vib-value').textContent = vib + ' Hz';
            document.getElementById('pressure-value').textContent = pressure + ' PSI';
            document.getElementById('current-value').textContent = current + ' A';
        }
        
        function addNewEvent() {
            const now = new Date();
            const temp = (20 + Math.random() * 60).toFixed(1);
            const vib = (Math.random() * 10).toFixed(1);
            const risk = (Math.random() * 100).toFixed(1);
            const statuses = ['OK', 'WARNING', 'CRITICAL'];
            const status = statuses[Math.floor(Math.random() * statuses.length)];
            
            const newEvent = {
                time: now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                machine: `SIM-Machine${Math.floor(Math.random() * 3) + 1}`,
                temp: temp + '°C',
                vib: vib,
                risk: risk + '%',
                status: status
            };
            
            allEvents.unshift(newEvent);
            allEvents = allEvents.slice(0, 20);
            renderEvents();
        }
        
        function renderEvents() {
            const tbody = document.getElementById('events-tbody');
            let filteredEvents = allEvents;
            
            if (currentFilter !== 'all') {
                filteredEvents = allEvents.filter(event => 
                    event.status.toLowerCase() === currentFilter.toLowerCase()
                );
            }
            
            tbody.innerHTML = filteredEvents.map(event => {
                const statusIcon = event.status === 'CRITICAL' ? '🔴' : 
                                 event.status === 'WARNING' ? '🟡' : '🟢';
                const statusClass = event.status === 'CRITICAL' ? 'status-critical' : 
                                   event.status === 'WARNING' ? 'status-warning' : 'status-ok';
                
                return `
                    <tr>
                        <td>${event.time}</td>
                        <td>${event.machine}</td>
                        <td>${event.temp}</td>
                        <td>${event.vib}</td>
                        <td>${event.risk}</td>
                        <td><span class="status-icon ${statusClass}">${statusIcon} ${event.status}</span></td>
                    </tr>
                `;
            }).join('');
        }
        
        function filterEvents(filter) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.filter-btn.' + filter).classList.add('active');
            renderEvents();
        }
        
        function showSection(section) {
            document.querySelectorAll('[id$="-section"]').forEach(el => el.style.display = 'none');
            document.getElementById(section + '-section').style.display = 'block';
            document.querySelectorAll('.sidebar-icon').forEach(icon => icon.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function exportEvents() {
            showToast('Events exported successfully!');
        }
        
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }
        
        // Start live updates
        setInterval(updateSensorValues, 3000);
        setInterval(addNewEvent, 8000);
        
        console.log('Dashboard loaded successfully - Live data updating every 3 seconds');
    </script>
</body>
</html>
"""

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return dashboard_html

@app.get("/api/sensors")
async def get_sensors():
    return {
        **sensor_data,
        "mode": sensor_manager.mode,
        "raspberry_pi": RASPBERRY_PI
    }

@app.get("/api/events")
async def get_events():
    return events_log

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sensor_manager.start_monitoring())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return dashboard_html

@app.get("/api/sensors")
async def get_sensors():
    return {
        **sensor_data,
        "mode": sensor_manager.mode,
        "raspberry_pi": RASPBERRY_PI
    }

@app.get("/api/events")
async def get_events():
    return events_log

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        # Send initial sensor data immediately upon connection
        await websocket.send_text(json.dumps({
            "type": "sensor_update",
            "data": {
                **sensor_data,
                "mode": sensor_manager.mode,
                "raspberry_pi": RASPBERRY_PI
            }
        }))
        
        while True:
            # Keep connection alive and listen for messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Echo back any received data
                await websocket.send_text(f"Received: {data}")
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "data": "connection_alive"
                }))
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

@app.on_event("startup")
async def startup_event():
    # Start sensor monitoring in background
    asyncio.create_task(sensor_manager.start_monitoring())

@app.on_event("shutdown")
async def shutdown_event():
    sensor_manager.running = False
    if RASPBERRY_PI:
        GPIO.cleanup()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
