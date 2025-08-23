"""
DS18B20 Temperature Sensor Reader
Handles communication with DS18B20 1-Wire temperature sensor on Raspberry Pi
"""

import time
import glob
import logging
from typing import Optional, List


class DS18B20Reader:
    """
    DS18B20 1-Wire temperature sensor reader for Raspberry Pi
    
    The DS18B20 sensor uses the 1-Wire protocol and typically connects to GPIO pin 4 (default)
    on Raspberry Pi. The sensor data is accessed through the w1 kernel modules.
    """
    
    def __init__(self, sensor_id: Optional[str] = None, base_dir: str = '/sys/bus/w1/devices/'):
        """
        Initialize DS18B20 sensor reader
        
        Args:
            sensor_id: Specific sensor ID (if None, uses first available sensor)
            base_dir: Base directory for 1-wire devices (default: /sys/bus/w1/devices/)
        """
        self.logger = logging.getLogger(__name__)
        self.base_dir = base_dir
        self.sensor_id = sensor_id
        self.device_folder = None
        self.device_file = None
        
        # Initialize sensor
        self._initialize_sensor()
    
    def _initialize_sensor(self):
        """Initialize and verify sensor connection"""
        try:
            if self.sensor_id:
                # Use specific sensor ID
                self.device_folder = f"{self.base_dir}{self.sensor_id}"
                self.device_file = f"{self.device_folder}/w1_slave"
            else:
                # Auto-detect first available DS18B20 sensor
                device_folders = glob.glob(f"{self.base_dir}28*")
                if not device_folders:
                    raise Exception("No DS18B20 sensors found. Check wiring and 1-Wire configuration.")
                
                self.device_folder = device_folders[0]
                self.device_file = f"{self.device_folder}/w1_slave"
                self.sensor_id = self.device_folder.split('/')[-1]
            
            self.logger.info(f"DS18B20 sensor initialized: {self.sensor_id}")
            
            # Test read to verify sensor is working
            test_temp = self._read_temp_raw()
            if test_temp is None:
                raise Exception("Failed to read from sensor during initialization")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize DS18B20 sensor: {e}")
            raise
    
    def _read_temp_raw(self) -> Optional[List[str]]:
        """
        Read raw temperature data from sensor file
        
        Returns:
            List of strings from sensor file, or None if read failed
        """
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            return lines
        except (FileNotFoundError, PermissionError, IOError) as e:
            self.logger.error(f"Failed to read sensor file {self.device_file}: {e}")
            return None
    
    def read_temperature(self, retries: int = 3) -> Optional[float]:
        """
        Read temperature from DS18B20 sensor
        
        Args:
            retries: Number of retry attempts if reading fails
            
        Returns:
            Temperature in Celsius, or None if reading failed
        """
        for attempt in range(retries):
            try:
                lines = self._read_temp_raw()
                if lines is None:
                    continue
                
                # Check if reading is valid (CRC check)
                while lines[0].strip()[-3:] != 'YES':
                    time.sleep(0.2)
                    lines = self._read_temp_raw()
                    if lines is None:
                        break
                
                if lines is None:
                    continue
                
                # Extract temperature value
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    
                    # Validate temperature reading (DS18B20 range: -55°C to +125°C)
                    if -55 <= temp_c <= 125:
                        return temp_c
                    else:
                        self.logger.warning(f"Temperature reading out of range: {temp_c}°C")
                        continue
                
            except (ValueError, IndexError, AttributeError) as e:
                self.logger.warning(f"Error parsing temperature data (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error reading temperature (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
                continue
        
        self.logger.error(f"Failed to read temperature after {retries} attempts")
        return None
    
    def get_sensor_info(self) -> dict:
        """
        Get sensor information
        
        Returns:
            Dictionary containing sensor information
        """
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': 'DS18B20',
            'device_file': self.device_file,
            'interface': '1-Wire'
        }
    
    def is_connected(self) -> bool:
        """
        Check if sensor is connected and responding
        
        Returns:
            True if sensor is connected and responding, False otherwise
        """
        try:
            temp = self.read_temperature(retries=1)
            return temp is not None
        except Exception:
            return False


# Mock implementation for testing on non-Raspberry Pi systems
class MockDS18B20Reader:
    """Mock DS18B20 reader for testing on systems without actual hardware"""
    
    def __init__(self, sensor_id: Optional[str] = None, base_dir: str = '/sys/bus/w1/devices/'):
        self.logger = logging.getLogger(__name__)
        self.sensor_id = sensor_id or "28-mock-sensor-id"
        self.logger.info(f"Mock DS18B20 sensor initialized: {self.sensor_id}")
    
    def read_temperature(self, retries: int = 3) -> Optional[float]:
        """Return mock temperature reading"""
        import random
        # Simulate realistic temperature readings (20-25°C with some variation)
        base_temp = 22.5
        variation = random.uniform(-2.5, 2.5)
        return round(base_temp + variation, 2)
    
    def get_sensor_info(self) -> dict:
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': 'DS18B20 (Mock)',
            'device_file': 'mock_device',
            'interface': '1-Wire (Mock)'
        }
    
    def is_connected(self) -> bool:
        return True
