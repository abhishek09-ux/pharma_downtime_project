#!/usr/bin/env python3
"""
DS18B20 Temperature Sensor Reader for Raspberry Pi
Real-time temperature monitoring with data logging and visualization
"""

import time
import json
import logging
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from sensor.ds18b20_reader import DS18B20Reader, MockDS18B20Reader
from data.data_logger import DataLogger
from config.settings import Config


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/temperature_monitor.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config()
    
    try:
        # Initialize temperature sensor
        logger.info("Initializing DS18B20 temperature sensor...")
        
        # Try to use real sensor, fall back to mock if needed
        if config.ENABLE_MOCK_SENSOR:
            sensor = MockDS18B20Reader(sensor_id=config.SENSOR_ID)
            logger.info("Using mock sensor for testing")
        else:
            try:
                sensor = DS18B20Reader(sensor_id=config.SENSOR_ID)
                logger.info("Real DS18B20 sensor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize real sensor: {e}")
                logger.info("Falling back to mock sensor")
                sensor = MockDS18B20Reader(sensor_id=config.SENSOR_ID)
        
        # Initialize data logger
        data_logger = DataLogger(config.DATA_FILE_PATH)
        
        logger.info(f"Starting temperature monitoring every {config.READ_INTERVAL} seconds...")
        logger.info("Press Ctrl+C to stop monitoring")
        
        while True:
            try:
                # Read temperature
                temperature = sensor.read_temperature()
                
                if temperature is not None:
                    # Create data record
                    data_record = {
                        'timestamp': datetime.now().isoformat(),
                        'temperature_celsius': round(temperature, 2),
                        'temperature_fahrenheit': round((temperature * 9/5) + 32, 2),
                        'sensor_id': config.SENSOR_ID
                    }
                    
                    # Log the reading
                    logger.info(f"Temperature: {temperature:.2f}°C ({data_record['temperature_fahrenheit']:.2f}°F)")
                    
                    # Save data
                    data_logger.log_data(data_record)
                    
                    # Check for alerts
                    if config.ENABLE_ALERTS:
                        check_temperature_alerts(temperature, config, logger)
                
                else:
                    logger.warning("Failed to read temperature from sensor")
                
                # Wait for next reading
                time.sleep(config.READ_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Temperature monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during temperature reading: {e}")
                time.sleep(config.READ_INTERVAL)
                
    except Exception as e:
        logger.error(f"Failed to initialize temperature monitoring: {e}")
        return 1
    
    logger.info("Temperature monitoring session ended")
    return 0


def check_temperature_alerts(temperature: float, config: Config, logger: logging.Logger):
    """Check temperature against alert thresholds"""
    if temperature > config.HIGH_TEMP_THRESHOLD:
        logger.warning(f"HIGH TEMPERATURE ALERT: {temperature:.2f}°C exceeds threshold of {config.HIGH_TEMP_THRESHOLD}°C")
    elif temperature < config.LOW_TEMP_THRESHOLD:
        logger.warning(f"LOW TEMPERATURE ALERT: {temperature:.2f}°C below threshold of {config.LOW_TEMP_THRESHOLD}°C")


if __name__ == "__main__":
    exit(main())
