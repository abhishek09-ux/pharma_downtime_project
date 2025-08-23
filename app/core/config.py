# app/core/config.py
import os
from typing import Optional

class Settings:
    """Application settings and configuration"""
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pharma.db")
    
    # Raspberry Pi configuration
    RASPBERRY_PI_MODE: bool = False
    
    # Sensor configuration
    DHT22_PIN: int = 18  # GPIO pin for DHT22 temperature sensor
    MCP3008_CHANNELS: dict = {
        "vibration_x": 0,  # ADXL335 X-axis on channel 0
        "vibration_y": 1,  # ADXL335 Y-axis on channel 1
        "vibration_z": 2,  # ADXL335 Z-axis on channel 2
        "current": 3       # ACS712 current sensor on channel 3
    }
    
    # I2C addresses
    I2C_ADDRESSES: dict = {
        "ads1115": 0x48,   # ADS1115 ADC
        "mlx90614": 0x5A,  # MLX90614 IR temperature sensor
        "ds3231": 0x68     # DS3231 RTC
    }
    
    # Sensor thresholds (pharma industry standards)
    THRESHOLDS: dict = {
        "temperature": {
            "normal_min": 20.0,
            "normal_max": 25.0,
            "warning_max": 30.0,
            "critical_max": 35.0
        },
        "machine_temperature": {
            "normal_min": 65.0,
            "normal_max": 80.0,
            "warning_max": 85.0,
            "critical_max": 90.0
        },
        "vibration": {
            "normal_max": 2.5,
            "warning_max": 4.0,
            "critical_max": 6.0
        },
        "humidity": {
            "normal_min": 40.0,
            "normal_max": 60.0,
            "warning_min": 30.0,
            "warning_max": 70.0
        },
        "current": {
            "normal_min": 1.0,
            "normal_max": 5.0,
            "warning_max": 8.0,
            "critical_max": 10.0
        }
    }
    
    # Machine configuration
    MACHINE_CONFIG: dict = {
        "default_machine_id": "Machine1",
        "shift_hours": {
            "day": {"start": 6, "end": 14},
            "evening": {"start": 14, "end": 22},
            "night": {"start": 22, "end": 6}
        }
    }
    
    # WebSocket configuration
    WEBSOCKET_PING_INTERVAL: int = 30
    SENSOR_READ_INTERVAL: int = 5  # seconds between sensor readings
    
    # ML Model configuration
    MODEL_PATH: str = "app/ml/downtime_model.pkl"
    MODEL_FEATURES: list = ["temperature", "vibration", "humidity", "shift"]
    
    def __init__(self):
        """Initialize settings and detect Raspberry Pi"""
        # Check for manual override environment variable
        if os.getenv("FORCE_RASPBERRY_PI", "false").lower() == "true":
            self.RASPBERRY_PI_MODE = True
        else:
            self.detect_raspberry_pi()
    
    def detect_raspberry_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            # Method 1: Check device tree model
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'rb') as f:
                    model = f.read().decode('utf-8', errors='ignore').strip('\x00')
                    if 'Raspberry Pi' in model:
                        self.RASPBERRY_PI_MODE = True
                        return
            
            # Method 2: Check /proc/cpuinfo for Pi-specific hardware
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    # Look for Raspberry Pi specific identifiers
                    pi_identifiers = ['bcm2', 'raspberry', 'arm']
                    if any(identifier in cpuinfo for identifier in pi_identifiers):
                        self.RASPBERRY_PI_MODE = True
                        return
            
            # Method 3: Check for Pi-specific directories
            pi_dirs = ['/sys/firmware/devicetree/base', '/opt/vc']
            if any(os.path.exists(d) for d in pi_dirs):
                self.RASPBERRY_PI_MODE = True
                return
                        
        except Exception as e:
            print(f"Pi detection error: {e}")
            pass
        
        self.RASPBERRY_PI_MODE = False

# Create global settings instance
settings = Settings()
