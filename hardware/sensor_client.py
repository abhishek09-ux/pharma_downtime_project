import asyncio
import json
import time
import websockets
import requests
from datetime import datetime
import logging
import math
import random
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running on Raspberry Pi
IS_RASPBERRY_PI = os.path.exists('/proc/device-tree/model') and 'Raspberry Pi' in open('/proc/device-tree/model', 'rb').read().decode('utf-8', errors='ignore')

# Only import hardware libraries on Raspberry Pi
if IS_RASPBERRY_PI:
    try:
        import board
        import busio
        import adafruit_dht
        import spidev
        import smbus2 as smbus
        HARDWARE_AVAILABLE = True
        logger.info("Running on Raspberry Pi - hardware libraries loaded")
    except ImportError as e:
        logger.warning(f"Hardware libraries not available: {e}")
        HARDWARE_AVAILABLE = False
else:
    logger.info("Running on non-Pi system - using simulated sensors")
    HARDWARE_AVAILABLE = False

class SensorManager:
    def __init__(self, machine_id="Machine1", server_url="ws://localhost:8000/ws/monitor"):
        self.machine_id = machine_id
        self.server_url = server_url
        self.api_base = server_url.replace("ws://", "http://").replace("/ws/monitor", "")
        
        # Initialize sensors
        self.setup_sensors()
        
    def setup_sensors(self):
        """Initialize all sensors"""
        try:
            if HARDWARE_AVAILABLE and IS_RASPBERRY_PI:
                # DHT22 Temperature/Humidity sensor (GPIO pin 4)
                self.dht22 = adafruit_dht.DHT22(board.D4)
                
                # I2C for MLX90614 IR temperature sensor
                self.i2c = busio.I2C(board.SCL, board.SDA)
                
                # ADXL335 vibration sensor (analog - using MCP3008 ADC)
                self.setup_vibration_sensor()
                
                logger.info("Hardware sensors initialized successfully")
            else:
                logger.info("Using simulated sensors for development")
                self.dht22 = None
                self.i2c = None
                self.spi = None
            
        except Exception as e:
            logger.error(f"Sensor initialization error: {e}")
            logger.info("Falling back to simulated sensors")
            self.dht22 = None
            self.i2c = None
            self.spi = None
            
    def setup_vibration_sensor(self):
        """Setup ADXL335 vibration sensor via MCP3008 ADC"""
        try:
            if HARDWARE_AVAILABLE:
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # Bus 0, Device 0
                self.spi.max_speed_hz = 1000000
                logger.info("ADXL335 vibration sensor ready")
            else:
                self.spi = None
        except Exception as e:
            logger.warning(f"spidev setup failed: {e}, using simulated vibration data")
            self.spi = None
            
    def read_mlx90614_temp(self):
        """Read temperature from MLX90614 IR sensor"""
        try:
            if HARDWARE_AVAILABLE and self.i2c:
                # MLX90614 I2C address is typically 0x5A
                bus = smbus.SMBus(1)
                
                # Read object temperature
                temp_object = bus.read_word_data(0x5A, 0x07)
                temp_object = temp_object * 0.02 - 273.15
                
                return round(temp_object, 2)
            else:
                # Simulated temperature with realistic patterns
                base_temp = 75  # Base machine temperature
                time_factor = math.sin(time.time() * 0.1) * 5  # Slow oscillation
                noise = random.uniform(-2, 3)
                return round(base_temp + time_factor + noise, 2)
                
        except Exception as e:
            logger.warning(f"MLX90614 read error: {e}, using simulated data")
            # Fallback to simulated temperature
            base_temp = 75
            time_factor = math.sin(time.time() * 0.1) * 5
            noise = random.uniform(-2, 3)
            return round(base_temp + time_factor + noise, 2)
            
    def read_dht22(self):
        """Read temperature and humidity from DHT22"""
        try:
            if HARDWARE_AVAILABLE and self.dht22:
                temperature = self.dht22.temperature
                humidity = self.dht22.humidity
                
                if temperature is not None and humidity is not None:
                    return round(temperature, 2), round(humidity, 2)
                else:
                    raise Exception("DHT22 returned None values")
            else:
                # Simulated environmental data
                base_temp = 22  # Room temperature
                temp_variation = math.sin(time.time() * 0.05) * 3
                temp_noise = random.uniform(-1, 2)
                temperature = round(base_temp + temp_variation + temp_noise, 2)
                
                base_humidity = 55  # Base humidity
                humidity_variation = math.cos(time.time() * 0.03) * 10
                humidity_noise = random.uniform(-3, 3)
                humidity = round(base_humidity + humidity_variation + humidity_noise, 2)
                
                return temperature, humidity
                
        except Exception as e:
            logger.warning(f"DHT22 read error: {e}, using simulated data")
            # Fallback to simulated data
            base_temp = 22
            temp_variation = math.sin(time.time() * 0.05) * 3
            temperature = round(base_temp + temp_variation + random.uniform(-1, 2), 2)
            
            base_humidity = 55
            humidity_variation = math.cos(time.time() * 0.03) * 10
            humidity = round(base_humidity + humidity_variation + random.uniform(-3, 3), 2)
            
            return temperature, humidity
            
    def read_adxl335_vibration(self):
        """Read vibration data from ADXL335"""
        try:
            if HARDWARE_AVAILABLE and self.spi:
                # Read X, Y, Z axes from MCP3008 channels 0, 1, 2
                x_raw = self.read_adc_channel(0)
                y_raw = self.read_adc_channel(1)
                z_raw = self.read_adc_channel(2)
                
                # Convert to G-force (assuming 3.3V supply, sensitivity ~300mV/g)
                x_g = (x_raw * 3.3 / 1024 - 1.65) / 0.3
                y_g = (y_raw * 3.3 / 1024 - 1.65) / 0.3
                z_g = (z_raw * 3.3 / 1024 - 1.65) / 0.3
                
                # Calculate total vibration magnitude
                vibration = math.sqrt(x_g**2 + y_g**2 + z_g**2)
                return round(vibration, 3)
            else:
                # Simulated vibration with realistic machine patterns
                base_vib = 1.8  # Base vibration level
                machine_cycle = math.sin(time.time() * 2) * 0.5  # Machine operation cycle
                random_spike = random.uniform(0, 1.2) if random.random() < 0.1 else 0  # Occasional spikes
                noise = random.uniform(-0.2, 0.3)
                vibration = base_vib + machine_cycle + random_spike + noise
                return round(max(0.5, vibration), 3)
                
        except Exception as e:
            logger.warning(f"ADXL335 read error: {e}, using simulated data")
            # Fallback to simulated vibration
            base_vib = 1.8
            machine_cycle = math.sin(time.time() * 2) * 0.5
            random_spike = random.uniform(0, 1.2) if random.random() < 0.1 else 0
            noise = random.uniform(-0.2, 0.3)
            vibration = base_vib + machine_cycle + random_spike + noise
            return round(max(0.5, vibration), 3)
            
    def read_adc_channel(self, channel):
        """Read single channel from MCP3008 ADC"""
        if not self.spi or channel < 0 or channel > 7:
            return random.randint(400, 600)  # Simulated ADC reading
            
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
        
    def calculate_risk_score(self, temp, humidity, vibration):
        """Calculate downtime risk based on sensor readings"""
        risk = 0.0
        
        # Temperature risk (optimal range: 70-80°C for machine temp)
        if temp > 85:
            risk += (temp - 85) * 0.03
        elif temp < 65:
            risk += (65 - temp) * 0.02
            
        # Humidity risk (optimal range: 40-60%)
        if humidity > 70:
            risk += (humidity - 70) * 0.01
        elif humidity < 30:
            risk += (30 - humidity) * 0.01
            
        # Vibration risk (normal < 2.5)
        if vibration > 2.5:
            risk += (vibration - 2.5) * 0.2
        elif vibration > 4.0:
            risk += (vibration - 2.5) * 0.4  # Critical vibration
            
        return min(1.0, max(0.0, risk))
        
    async def collect_sensor_data(self):
        """Collect data from all sensors"""
        try:
            # Read environmental sensors
            dht_temp, humidity = self.read_dht22()
            
            # Read machine temperature (IR sensor)
            machine_temp = self.read_mlx90614_temp()
            
            # Read vibration
            vibration = self.read_adxl335_vibration()
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(machine_temp, humidity, vibration)
            
            # Determine shift (simple time-based)
            hour = datetime.now().hour
            if 6 <= hour < 14:
                shift = 1
            elif 14 <= hour < 22:
                shift = 2
            else:
                shift = 3
                
            sensor_data = {
                "timestamp": datetime.now().isoformat(),
                "machine_id": self.machine_id,
                "temperature": machine_temp,
                "ambient_temp": dht_temp,
                "humidity": humidity,
                "vibration": vibration,
                "machine_load": round(70 + vibration * 8, 1),  # Simulated load based on vibration
                "shift": shift,
                "downtime_probability": round(risk_score, 3),
                "sensor_status": "online" if HARDWARE_AVAILABLE else "simulated"
            }
            
            logger.info(f"Sensor data: Temp={machine_temp}°C, Humidity={humidity}%, Vib={vibration}g, Risk={risk_score}")
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error collecting sensor data: {e}")
            return None
            
    async def send_to_api(self, data):
        """Send sensor data to FastAPI backend"""
        try:
            # Send prediction request
            response = requests.get(f"{self.api_base}/predict", params={
                "temperature": data["temperature"],
                "vibration": data["vibration"],
                "load": data["machine_load"],
                "shift": data["shift"]
            }, timeout=5)
            
            if response.status_code == 200:
                prediction = response.json()
                data["ml_prediction"] = prediction
                logger.info(f"ML Prediction: {prediction.get('downtime_predicted', 'N/A')}")
            
        except Exception as e:
            logger.warning(f"API request failed: {e}")
            
    async def send_to_websocket(self, data):
        """Send real-time data via WebSocket"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                message = {
                    "type": "sensor_update",
                    **data
                }
                await websocket.send(json.dumps(message))
                logger.info("Data sent via WebSocket")
                
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting sensor monitoring for {self.machine_id}")
        logger.info(f"Hardware mode: {'Real sensors' if HARDWARE_AVAILABLE else 'Simulated'}")
        
        while True:
            try:
                # Collect sensor data
                sensor_data = await self.collect_sensor_data()
                
                if sensor_data:
                    # Send to API for ML prediction
                    await self.send_to_api(sensor_data)
                    
                    # Send real-time update via WebSocket
                    await self.send_to_websocket(sensor_data)
                    
                # Wait 5 seconds before next reading
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error

if __name__ == "__main__":
    # Configuration - you can change these
    MACHINE_ID = "Machine1"  # Change this for different machines
    SERVER_URL = "ws://localhost:8000/ws/monitor"  # Use localhost for development
    
    # Create sensor manager
    sensor_manager = SensorManager(MACHINE_ID, SERVER_URL)
    
    # Run monitoring
    asyncio.run(sensor_manager.run_monitoring_loop())
