import csv
from typing import List, Set, Dict, Any
from datetime import datetime
import random
import asyncio
import json
import logging
import os
import warnings
from contextlib import asynccontextmanager

# Suppress sklearn warnings for production
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# Set up logger
logger = logging.getLogger("pharma_downtime")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import configuration
from app.core.config import settings

# Create lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting sensor monitoring...")
    task = asyncio.create_task(sensor_manager.start_monitoring())
    yield
    # Shutdown
    logger.info("🛑 Shutting down sensor monitoring...")
    sensor_manager.running = False
    task.cancel()
    if RASPBERRY_PI and hardware_sensors:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("🧹 GPIO cleanup completed")
        except:
            pass

app = FastAPI(
    title="Pharma Downtime Monitoring System",
    lifespan=lifespan
)

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
    "temperature": {"value": 22.5, "status": "offline", "unit": "°C", "type": "ambient"},
    "machine_temperature": {"value": 75.0, "status": "offline", "unit": "°C", "type": "machine"},
    "vibration": {"value": 1.8, "status": "offline", "unit": "G", "type": "acceleration"},
    "humidity": {"value": 55.0, "status": "offline", "unit": "%", "type": "relative"},
    "current": {"value": 3.2, "status": "offline", "unit": "A", "type": "electrical"},
    "load": {"value": 75.0, "status": "offline", "unit": "%", "type": "machine_load"}
}

events_log = []

# Determine if we're running on Raspberry Pi
RASPBERRY_PI = settings.RASPBERRY_PI_MODE
hardware_sensors = None

# Check for manual Pi mode override
FORCE_PI_MODE = os.getenv("FORCE_RASPBERRY_PI", "false").lower() == "true"

if FORCE_PI_MODE:
    logger.info("🔧 FORCE_RASPBERRY_PI enabled - Running in Pi mode without hardware")
    RASPBERRY_PI = True

# Try to import Raspberry Pi libraries and configure hardware
if RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
        import board
        import busio
        import adafruit_dht
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        import time
        
        logger.info("✅ Raspberry Pi libraries loaded - REAL SENSOR MODE")
        
        # CONFIGURE ACTUAL RASPBERRY PI HARDWARE (skip if forced mode)
        if not FORCE_PI_MODE:
            try:
                # GPIO Setup
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # DHT22 Temperature/Humidity sensor on configured GPIO pin
                dht22 = adafruit_dht.DHT22(getattr(board, f'D{settings.DHT22_PIN}'))
                
                # I2C Setup for ADC
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c, address=settings.I2C_ADDRESSES["ads1115"])
                
                # Analog sensor channels based on configuration
                vibration_x_channel = AnalogIn(ads, getattr(ADS, f'P{settings.MCP3008_CHANNELS["vibration_x"]}'))
                vibration_y_channel = AnalogIn(ads, getattr(ADS, f'P{settings.MCP3008_CHANNELS["vibration_y"]}'))
                vibration_z_channel = AnalogIn(ads, getattr(ADS, f'P{settings.MCP3008_CHANNELS["vibration_z"]}'))
                current_channel = AnalogIn(ads, getattr(ADS, f'P{settings.MCP3008_CHANNELS["current"]}'))
                
                # Store hardware references
                hardware_sensors = {
                    'dht22': dht22,
                    'ads': ads,
                    'vibration_channels': [vibration_x_channel, vibration_y_channel, vibration_z_channel],
                    'current_channel': current_channel
                }
                
                logger.info(f"🔧 Raspberry Pi GPIO and sensors configured successfully")
                logger.info(f"📍 DHT22 on GPIO {settings.DHT22_PIN}, ADS1115 on I2C address {hex(settings.I2C_ADDRESSES['ads1115'])}")
                
            except Exception as e:
                logger.error(f"❌ Hardware configuration failed: {e}")
                if not FORCE_PI_MODE:
                    RASPBERRY_PI = False
                    hardware_sensors = None
        else:
            logger.info("⚠️ Hardware configuration skipped in FORCE mode")
            
    except ImportError as e:
        if not FORCE_PI_MODE:
            RASPBERRY_PI = False
            hardware_sensors = None
            logger.info(f"⚠️ Pi libraries not available: {e}")
        else:
            logger.info(f"⚠️ Pi libraries not available in forced mode: {e}")
            # Keep RASPBERRY_PI = True but hardware_sensors = None
else:
    logger.info("⚠️ Running in SIMULATION MODE - Not detected as Raspberry Pi")

class SensorManager:
    def __init__(self):
        self.running = False
        self.mode = "REAL SENSORS" if RASPBERRY_PI else "SIMULATION"
        self.read_errors = 0
        self.hardware = hardware_sensors
        logger.info(f"🚀 SensorManager initialized in {self.mode} mode")
        
    def read_real_dht22(self):
        """Read DHT22 ambient temperature and humidity"""
        if not self.hardware or not self.hardware.get('dht22'):
            return None, None
            
        try:
            dht22 = self.hardware['dht22']
            temperature = dht22.temperature
            humidity = dht22.humidity
            return temperature, humidity
        except Exception as e:
            logger.warning(f"DHT22 read error: {e}")
            return None, None
    
    def read_real_vibration(self):
        """Read ADXL335 vibration sensor (3-axis accelerometer)"""
        if not self.hardware or not self.hardware.get('vibration_channels'):
            return None
            
        try:
            channels = self.hardware['vibration_channels']
            
            # Read X, Y, Z axes
            x_voltage = channels[0].voltage
            y_voltage = channels[1].voltage  
            z_voltage = channels[2].voltage
            
            # Convert to G-force (ADXL335: 330mV/g, 1.65V = 0g)
            x_g = (x_voltage - 1.65) / 0.33
            y_g = (y_voltage - 1.65) / 0.33
            z_g = (z_voltage - 1.65) / 0.33
            
            # Calculate total vibration magnitude
            import math
            vibration = math.sqrt(x_g**2 + y_g**2 + z_g**2)
            return vibration
            
        except Exception as e:
            logger.warning(f"Vibration sensor read error: {e}")
            return None
    
    def read_real_current(self):
        """Read ACS712 current sensor"""
        if not self.hardware or not self.hardware.get('current_channel'):
            return None, None
            
        try:
            channel = self.hardware['current_channel']
            voltage = channel.voltage
            
            # ACS712-20A: 2.5V = 0A, 100mV/A sensitivity
            current = abs((voltage - 2.5) / 0.1)
            
            # Calculate load percentage (assuming 8A = 100% load for pharma equipment)
            load_percentage = min(100.0, (current / 8.0) * 100)
            
            return current, load_percentage
            
        except Exception as e:
            logger.warning(f"Current sensor read error: {e}")
            return None, None
    
    def get_realistic_simulation_data(self):
        """Generate realistic simulation data based on pharma industry patterns"""
        import math
        import time
        
        # Time-based patterns for realistic simulation
        current_time = time.time()
        
        # Ambient temperature (office/lab environment: 20-26°C)
        base_temp = 22.0
        daily_temp_cycle = math.sin(current_time * 0.0001) * 3  # Slow daily variation
        temp_noise = random.uniform(-0.5, 0.5)
        ambient_temp = base_temp + daily_temp_cycle + temp_noise
        
        # Machine temperature (pharmaceutical equipment: 70-85°C normal operation)
        base_machine_temp = 75.0
        machine_cycle = math.sin(current_time * 0.01) * 5  # Machine operation cycles
        machine_noise = random.uniform(-1, 2)
        machine_temp = base_machine_temp + machine_cycle + machine_noise
        
        # Humidity (controlled pharma environment: 45-65%)
        base_humidity = 55.0
        humidity_cycle = math.cos(current_time * 0.0005) * 8
        humidity_noise = random.uniform(-2, 2)
        humidity = base_humidity + humidity_cycle + humidity_noise
        
        # Vibration (pharmaceutical equipment: 0.5-3.0G normal)
        base_vibration = 1.5
        vibration_cycle = math.sin(current_time * 2) * 0.8  # Machine vibration cycles
        random_spike = random.uniform(0, 1.5) if random.random() < 0.05 else 0  # Occasional spikes
        vibration_noise = random.uniform(-0.2, 0.3)
        vibration = base_vibration + vibration_cycle + random_spike + vibration_noise
        vibration = max(0.2, vibration)  # Minimum vibration
        
        # Current (pharmaceutical equipment: 2-6A normal operation)
        base_current = 3.5
        current_cycle = math.sin(current_time * 0.02) * 1.0
        current_noise = random.uniform(-0.3, 0.5)
        current = base_current + current_cycle + current_noise
        current = max(1.0, min(8.0, current))
        
        # Load percentage based on current
        load_percentage = (current / 8.0) * 100
        
        return {
            'ambient_temp': round(ambient_temp, 1),
            'machine_temp': round(machine_temp, 1), 
            'humidity': round(humidity, 1),
            'vibration': round(vibration, 2),
            'current': round(current, 2),
            'load': round(load_percentage, 1)
        }
        
    async def read_sensors(self):
        """Read data from all sensors - real or simulated"""
        global sensor_data
        
        if RASPBERRY_PI and self.hardware:
            try:
                # Read REAL sensors
                amb_temp, humidity = self.read_real_dht22()
                vibration = self.read_real_vibration()
                current, load = self.read_real_current()
                
                # Update sensor data with real readings
                if amb_temp is not None:
                    sensor_data["temperature"]["value"] = round(amb_temp, 1)
                    sensor_data["temperature"]["status"] = "online"
                else:
                    sensor_data["temperature"]["status"] = "error"
                
                if humidity is not None:
                    sensor_data["humidity"]["value"] = round(humidity, 1)
                    sensor_data["humidity"]["status"] = "online"
                else:
                    sensor_data["humidity"]["status"] = "error"
                
                if vibration is not None:
                    sensor_data["vibration"]["value"] = round(vibration, 2)
                    sensor_data["vibration"]["status"] = "online"
                else:
                    sensor_data["vibration"]["status"] = "error"
                
                if current is not None and load is not None:
                    sensor_data["current"]["value"] = round(current, 2)
                    sensor_data["current"]["status"] = "online"
                    sensor_data["load"]["value"] = round(load, 1)
                    sensor_data["load"]["status"] = "online"
                else:
                    sensor_data["current"]["status"] = "error"
                    sensor_data["load"]["status"] = "error"
                
                # Machine temperature would need IR sensor (simulated for now)
                sim_data = self.get_realistic_simulation_data()
                sensor_data["machine_temperature"]["value"] = sim_data['machine_temp']
                sensor_data["machine_temperature"]["status"] = "simulated"
                
                self.read_errors = 0
                logger.debug(f"🌡️ Real sensors: T={amb_temp}°C, H={humidity}%, V={vibration}G, I={current}A")
                
            except Exception as e:
                self.read_errors += 1
                logger.error(f"❌ Sensor read error #{self.read_errors}: {e}")
                
                # Fall back to simulation after 3 consecutive errors
                if self.read_errors >= 3:
                    for sensor in sensor_data:
                        sensor_data[sensor]["status"] = "offline"
                        
        else:
            # SIMULATION MODE - Use realistic pharmaceutical industry data
            sim_data = self.get_realistic_simulation_data()
            
            sensor_data["temperature"]["value"] = sim_data['ambient_temp']
            sensor_data["temperature"]["status"] = "simulated"
            
            sensor_data["machine_temperature"]["value"] = sim_data['machine_temp']
            sensor_data["machine_temperature"]["status"] = "simulated"
            
            sensor_data["humidity"]["value"] = sim_data['humidity']
            sensor_data["humidity"]["status"] = "simulated"
            
            sensor_data["vibration"]["value"] = sim_data['vibration']
            sensor_data["vibration"]["status"] = "simulated"
            
            sensor_data["current"]["value"] = sim_data['current']
            sensor_data["current"]["status"] = "simulated"
            
            sensor_data["load"]["value"] = sim_data['load']
            sensor_data["load"]["status"] = "simulated"
    
    def calculate_downtime_risk(self):
        """Calculate downtime risk using enhanced ML model + rule-based system"""
        try:
            # Get current sensor values
            amb_temp = sensor_data["temperature"]["value"]
            machine_temp = sensor_data["machine_temperature"]["value"]
            humidity = sensor_data["humidity"]["value"]
            vibration = sensor_data["vibration"]["value"]
            current = sensor_data["current"]["value"]
            
            # Get current shift
            current_hour = datetime.now().hour
            if 6 <= current_hour < 14:
                shift = 1  # Day
            elif 14 <= current_hour < 22:
                shift = 2  # Evening
            else:
                shift = 3  # Night
            
            # Try to use ML model for prediction
            try:
                from app.ml.model import predict_downtime
                ml_result = predict_downtime(amb_temp, machine_temp, humidity, vibration, current, shift)
                ml_risk = ml_result['downtime_probability']
                
                # Use ML prediction as base risk
                risk_score = ml_risk
                
                logger.debug(f"🤖 ML Risk: {ml_risk:.3f} ({ml_result['risk_level']})")
                
            except Exception as e:
                logger.warning(f"ML prediction failed, using rule-based: {e}")
                
                # Fallback to rule-based risk calculation
                risk_score = 0.0
                
                # Temperature risk assessment (ambient)
                temp_thresholds = settings.THRESHOLDS["temperature"]
                if amb_temp > temp_thresholds["critical_max"]:
                    risk_score += 0.3
                elif amb_temp > temp_thresholds["warning_max"]:
                    risk_score += 0.15
                elif amb_temp < temp_thresholds["normal_min"]:
                    risk_score += 0.1
                
                # Machine temperature risk
                machine_temp_thresholds = settings.THRESHOLDS["machine_temperature"]
                if machine_temp > machine_temp_thresholds["critical_max"]:
                    risk_score += 0.4
                elif machine_temp > machine_temp_thresholds["warning_max"]:
                    risk_score += 0.2
                elif machine_temp < machine_temp_thresholds["normal_min"]:
                    risk_score += 0.15
                
                # Humidity risk
                humidity_thresholds = settings.THRESHOLDS["humidity"]
                if humidity > humidity_thresholds["warning_max"]:
                    risk_score += 0.15
                elif humidity < humidity_thresholds["warning_min"]:
                    risk_score += 0.1
                
                # Vibration risk (critical for pharmaceutical equipment)
                vibration_thresholds = settings.THRESHOLDS["vibration"]
                if vibration > vibration_thresholds["critical_max"]:
                    risk_score += 0.5
                elif vibration > vibration_thresholds["warning_max"]:
                    risk_score += 0.25
                elif vibration > vibration_thresholds["normal_max"]:
                    risk_score += 0.1
                
                # Current/electrical risk
                current_thresholds = settings.THRESHOLDS["current"]
                if current > current_thresholds["critical_max"]:
                    risk_score += 0.3
                elif current > current_thresholds["warning_max"]:
                    risk_score += 0.15
                
                # Shift-based risk adjustment
                if shift == 3:  # Night shift
                    risk_score += 0.08
                elif shift == 2:  # Evening shift
                    risk_score += 0.03
            
            return min(1.0, max(0.0, risk_score))
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            return 0.2  # Default low risk
    
    def get_status_from_risk(self, risk_score):
        """Determine equipment status based on risk score"""
        if risk_score >= 0.7:
            return "CRITICAL"
        elif risk_score >= 0.4:
            return "WARNING"
        else:
            return "OK"
    
    async def log_event(self):
        """Log sensor readings as events with realistic pharma data and save to database"""
        global events_log
        
        now = datetime.now()
        risk_score = self.calculate_downtime_risk()
        status = self.get_status_from_risk(risk_score)
        
        # Get current sensor values
        amb_temp = sensor_data["temperature"]["value"]
        machine_temp = sensor_data["machine_temperature"]["value"]
        vibration = sensor_data["vibration"]["value"]
        load = sensor_data["load"]["value"]
        
        # Determine machine prefix based on actual mode
        machine_prefix = "PI-" if RASPBERRY_PI else "SIM-"
        
        # Create realistic machine names for pharmaceutical environment
        machine_names = [
            f"{machine_prefix}Tablet-Press-1",
            f"{machine_prefix}Capsule-Filler-2", 
            f"{machine_prefix}Coating-Pan-1",
            f"{machine_prefix}Granulator-A",
            f"{machine_prefix}Mixer-B1"
        ]
        
        machine_name = random.choice(machine_names)
        
        event = {
            "time": now.strftime("%I:%M %p"),
            "machine": machine_name,
            "ambient_temp": f"{amb_temp}°C",
            "machine_temp": f"{machine_temp}°C", 
            "vibration": f"{vibration}G",
            "load": f"{load}%",
            "risk": f"{risk_score*100:.1f}%",
            "status": status,
            "timestamp": now.isoformat(),
            "mode": self.mode,
            "raspberry_pi": RASPBERRY_PI
        }
        
        events_log.insert(0, event)
        events_log = events_log[:50]  # Keep last 50 events
        
        # Save to database every 10th reading (to avoid too frequent DB writes)
        if len(events_log) % 10 == 0:
            try:
                from app.services.database_service import db_service
                db_service.save_sensor_reading(sensor_data, machine_name)
                
                # Save downtime event if critical
                if status == "CRITICAL":
                    db_service.save_downtime_event(
                        machine_name, 
                        f"Critical conditions: Risk={risk_score*100:.1f}%",
                        duration_minutes=0.0
                    )
                    
            except Exception as e:
                logger.warning(f"Database logging failed: {e}")
        
        # Send to connected websockets
        for websocket in connected_websockets:
            try:
                await websocket.send_text(json.dumps({
                    "type": "new_event",
                    "data": event
                }))
            except:
                connected_websockets.remove(websocket) if websocket in connected_websockets else None
    
    async def start_monitoring(self):
        """Start continuous sensor monitoring"""
        self.running = True
        logger.info(f"🔄 Starting sensor monitoring in {self.mode} mode...")
        
        while self.running:
            await self.read_sensors()
            await self.log_event()
            
            # Send sensor updates via websocket
            for websocket in connected_websockets:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "sensor_update",
                        "data": {
                            **sensor_data,
                            "mode": self.mode,
                            "raspberry_pi": RASPBERRY_PI
                        }
                    }))
                except:
                    pass
            
            await asyncio.sleep(2 if RASPBERRY_PI else 3)  # Faster on real Pi

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
        .status-indicator { font-size: 0.8rem; margin-left: 8px; }
        .status-online { color: #10b981; }
        .status-offline { color: #ef4444; }
        .status-error { color: #f59e0b; }
        .status-simulated { color: #6b7280; }
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
                <div class="mode-badge" id="connection-status">🔍 DETECTING...</div>
                <div class="mode-badge" id="pi-status" style="background: #6b7280;">📱 CHECKING PI...</div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button class="btn" style="background: #2563eb; color: white;" onclick="showToast('Add Machine modal opened!')">Add Machine</button>
                <button class="btn" style="background: #1e40af; color: white;" onclick="showToast('Admin panel accessed!')">Admin</button>
                <div style="background: #2563eb; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;" onclick="showToast('User profile opened!')">👤</div>
            </div>
        </header>

        <div class="dashboard-content" id="dashboard-section">
            <div class="metrics-grid">
                <div class="metric-card" style="border-left-color: #3b82f6;">
                    <div class="metric-header">Ambient Temperature</div>
                    <div class="metric-value">
                        <span style="color: #3b82f6;">🌡️</span>
                        <span id="temp-value">22.5°C</span>
                        <span id="temp-status" class="status-indicator">⚫</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #ef4444;">
                    <div class="metric-header">Machine Temperature</div>
                    <div class="metric-value">
                        <span style="color: #ef4444;">🔥</span>
                        <span id="machine-temp-value">75.0°C</span>
                        <span id="machine-temp-status" class="status-indicator">⚫</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #f59e0b;">
                    <div class="metric-header">Vibration</div>
                    <div class="metric-value">
                        <span style="color: #f59e0b;">📳</span>
                        <span id="vib-value">1.8 G</span>
                        <span id="vib-status" class="status-indicator">⚫</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #06b6d4;">
                    <div class="metric-header">Humidity</div>
                    <div class="metric-value">
                        <span style="color: #06b6d4;">�</span>
                        <span id="humidity-value">55.0%</span>
                        <span id="humidity-status" class="status-indicator">⚫</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #2563eb;">
                    <div class="metric-header">Current</div>
                    <div class="metric-value">
                        <span style="color: #2563eb;">⚡</span>
                        <span id="current-value">3.2 A</span>
                        <span id="current-status" class="status-indicator">⚫</span>
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #10b981;">
                    <div class="metric-header">Machine Load</div>
                    <div class="metric-value">
                        <span style="color: #10b981;">📊</span>
                        <span id="load-value">75.0%</span>
                        <span id="load-status" class="status-indicator">⚫</span>
                    </div>
                </div>
            </div>

            <div class="content-grid">
                <div class="chart-section">
                    <h3>📈 Live Sensor Status</h3>
                    <div style="margin: 20px 0;">
                        <div>Ambient Temperature: <span id="ambient-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div>Machine Temperature: <span id="machine-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div>Vibration Sensor: <span id="vibration-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div>Humidity Sensor: <span id="humidity-sensor-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div>Current Sensor: <span id="current-sensor-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div>Load Monitor: <span id="load-sensor-status" style="color: #6b7280; font-weight: bold;">Initializing...</span></div>
                        <div style="margin-top: 15px; padding: 10px; background: #f8fafc; border-radius: 8px;">
                            <strong>Connection:</strong> <span id="connection-info">Connecting...</span><br>
                            <strong>Hardware:</strong> <span id="hardware-info">Detecting...</span>
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
                                <th>Ambient</th>
                                <th>Machine</th>
                                <th>Vibration</th>
                                <th>Load</th>
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
        let allEvents = [];
        let websocket = null;
        
        // Connect to WebSocket for real-time updates
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function(event) {
                console.log('WebSocket connected');
                showToast('Connected to live sensor data');
            };
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'sensor_update') {
                    updateSensorDisplay(data.data);
                } else if (data.type === 'new_event') {
                    addEventToTable(data.data);
                }
            };
            
            websocket.onclose = function(event) {
                console.log('WebSocket disconnected, attempting to reconnect...');
                setTimeout(connectWebSocket, 3000);
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateSensorDisplay(sensorData) {
            // Update connection and Pi status
            const connectionStatus = document.getElementById('connection-status');
            const piStatus = document.getElementById('pi-status');
            
            if (sensorData.raspberry_pi) {
                connectionStatus.textContent = '🔗 CONNECTED';
                connectionStatus.style.background = '#10b981';
                piStatus.textContent = '🍓 RASPBERRY PI';
                piStatus.style.background = '#059669';
            } else {
                connectionStatus.textContent = '🎭 SIMULATION';
                connectionStatus.style.background = '#f59e0b';
                piStatus.textContent = '💻 DEVELOPMENT';
                piStatus.style.background = '#6b7280';
            }
            
            // Update detailed status info
            document.getElementById('connection-info').textContent = sensorData.mode;
            document.getElementById('hardware-info').textContent = sensorData.raspberry_pi ? 'Raspberry Pi 4B' : 'Development PC';
            
            // Update sensor values and status indicators
            updateSensorValue('temp', sensorData.temperature);
            updateSensorValue('machine-temp', sensorData.machine_temperature);
            updateSensorValue('vib', sensorData.vibration);
            updateSensorValue('humidity', sensorData.humidity);
            updateSensorValue('current', sensorData.current);
            updateSensorValue('load', sensorData.load);
            
            // Update detailed sensor status
            updateDetailedStatus('ambient-status', sensorData.temperature);
            updateDetailedStatus('machine-status', sensorData.machine_temperature);
            updateDetailedStatus('vibration-status', sensorData.vibration);
            updateDetailedStatus('humidity-sensor-status', sensorData.humidity);
            updateDetailedStatus('current-sensor-status', sensorData.current);
            updateDetailedStatus('load-sensor-status', sensorData.load);
        }
        
        function updateDetailedStatus(elementId, sensorInfo) {
            const element = document.getElementById(elementId);
            if (element && sensorInfo) {
                let statusText = '';
                let color = '';
                
                switch(sensorInfo.status) {
                    case 'online':
                        statusText = 'Online (Real Sensor)';
                        color = '#10b981';
                        break;
                    case 'offline':
                        statusText = 'Offline';
                        color = '#ef4444';
                        break;
                    case 'error':
                        statusText = 'Error - Check Connection';
                        color = '#f59e0b';
                        break;
                    case 'simulated':
                        statusText = 'Simulated Data';
                        color = '#6b7280';
                        break;
                    default:
                        statusText = 'Unknown';
                        color = '#6b7280';
                        break;
                }
                
                element.textContent = statusText;
                element.style.color = color;
            }
        }
        
        function updateSensorValue(sensorType, sensorInfo) {
            const valueElement = document.getElementById(`${sensorType}-value`);
            const statusElement = document.getElementById(`${sensorType}-status`);
            
            if (valueElement && sensorInfo) {
                valueElement.textContent = `${sensorInfo.value}${sensorInfo.unit}`;
                
                if (statusElement) {
                    statusElement.className = 'status-indicator';
                    
                    switch(sensorInfo.status) {
                        case 'online':
                            statusElement.textContent = '🟢';
                            statusElement.classList.add('status-online');
                            break;
                        case 'offline':
                            statusElement.textContent = '🔴';
                            statusElement.classList.add('status-offline');
                            break;
                        case 'error':
                            statusElement.textContent = '🟡';
                            statusElement.classList.add('status-error');
                            break;
                        case 'simulated':
                            statusElement.textContent = '🔵';
                            statusElement.classList.add('status-simulated');
                            break;
                        default:
                            statusElement.textContent = '⚫';
                            break;
                    }
                }
            }
        }
        
        function addEventToTable(event) {
            allEvents.unshift(event);
            allEvents = allEvents.slice(0, 50); // Keep last 50 events
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
                        <td>${event.ambient_temp}</td>
                        <td>${event.machine_temp}</td>
                        <td>${event.vibration}</td>
                        <td>${event.load}</td>
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
            const dataStr = JSON.stringify(allEvents, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `pharma_events_${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            showToast('Events exported successfully!');
        }
        
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            console.log('Pharma Downtime Dashboard loaded - Connecting to live sensor data...');
        });
    </script>
</body>
</html>
"""

# API Routes
from app.routes.predict import router as predict_router
from app.routes.dashboard_api import router as dashboard_router

app.include_router(predict_router)
app.include_router(dashboard_router)

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
        # Send initial data
        await websocket.send_text(json.dumps({
            "type": "sensor_update",
            "data": {
                **sensor_data,
                "mode": sensor_manager.mode,
                "raspberry_pi": RASPBERRY_PI
            }
        }))
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                await websocket.send_text(f"Received: {data}")
            except asyncio.TimeoutError:
                # Keep alive ping
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

if __name__ == "__main__":
    logger.info("🚀 Starting Pharma Downtime Monitoring System...")
    logger.info(f"📍 Mode: {sensor_manager.mode}")
    logger.info(f"🔧 Raspberry Pi: {'Yes' if RASPBERRY_PI else 'No'}")
    logger.info("🌐 Dashboard will be available at: http://localhost:8000")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=False  # Set to True for development
    )
