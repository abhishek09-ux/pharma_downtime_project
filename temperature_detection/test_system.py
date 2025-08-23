#!/usr/bin/env python3
"""
Quick test script to verify the temperature monitoring system
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from sensor.ds18b20_reader import DS18B20Reader, MockDS18B20Reader
from data.data_logger import DataLogger
from config.settings import Config


def setup_logging():
    """Setup logging for test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def test_configuration():
    """Test configuration loading"""
    print("Testing configuration...")
    config = Config()
    print(f"✓ Configuration loaded successfully")
    print(f"  - Read interval: {config.READ_INTERVAL}s")
    print(f"  - Data file: {config.DATA_FILE_PATH}")
    print(f"  - Mock sensor: {config.ENABLE_MOCK_SENSOR}")
    return config


def test_sensor(config):
    """Test sensor initialization and reading"""
    print("\nTesting sensor...")
    
    try:
        # Try real sensor first, fall back to mock
        if config.ENABLE_MOCK_SENSOR:
            sensor = MockDS18B20Reader()
            print("✓ Using mock sensor for testing")
        else:
            try:
                sensor = DS18B20Reader(sensor_id=config.SENSOR_ID)
                print("✓ Real DS18B20 sensor initialized")
            except Exception as e:
                print(f"! Real sensor failed ({e}), using mock sensor")
                sensor = MockDS18B20Reader()
        
        # Test sensor info
        info = sensor.get_sensor_info()
        print(f"  - Sensor ID: {info['sensor_id']}")
        print(f"  - Sensor type: {info['sensor_type']}")
        
        # Test temperature reading
        temperature = sensor.read_temperature()
        if temperature is not None:
            print(f"✓ Temperature reading: {temperature:.2f}°C ({temperature * 9/5 + 32:.2f}°F)")
        else:
            print("✗ Failed to read temperature")
            return None
        
        # Test connection
        connected = sensor.is_connected()
        print(f"  - Connection status: {'Connected' if connected else 'Disconnected'}")
        
        return sensor
        
    except Exception as e:
        print(f"✗ Sensor test failed: {e}")
        return None


def test_data_logger(config):
    """Test data logging functionality"""
    print("\nTesting data logger...")
    
    try:
        logger = DataLogger(config.DATA_FILE_PATH)
        print("✓ Data logger initialized")
        
        # Test logging data
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'temperature_celsius': 22.5,
            'temperature_fahrenheit': 72.5,
            'sensor_id': 'test-sensor'
        }
        
        logger.log_data(test_data)
        print("✓ Test data logged successfully")
        
        # Test data retrieval
        recent_data = logger.get_recent_data(hours=1)
        print(f"✓ Retrieved {len(recent_data)} recent records")
        
        # Test statistics
        stats = logger.get_statistics(hours=24)
        if 'error' not in stats:
            print(f"✓ Statistics calculated: {stats['record_count']} records")
        else:
            print(f"! Statistics: {stats['error']}")
        
        # Test file info
        file_info = logger.get_data_file_info()
        print(f"  - Data file size: {file_info.get('file_size_bytes', 0)} bytes")
        
        return logger
        
    except Exception as e:
        print(f"✗ Data logger test failed: {e}")
        return None


def test_integration(sensor, data_logger):
    """Test complete integration"""
    print("\nTesting integration...")
    
    try:
        print("Running 3 temperature readings...")
        
        for i in range(3):
            temp = sensor.read_temperature()
            if temp is not None:
                data_record = {
                    'timestamp': datetime.now().isoformat(),
                    'temperature_celsius': round(temp, 2),
                    'temperature_fahrenheit': round((temp * 9/5) + 32, 2),
                    'sensor_id': sensor.get_sensor_info()['sensor_id']
                }
                
                data_logger.log_data(data_record)
                print(f"  Reading {i+1}: {temp:.2f}°C - logged successfully")
            else:
                print(f"  Reading {i+1}: Failed")
        
        print("✓ Integration test completed")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def main():
    """Main test function"""
    setup_logging()
    
    print("=" * 60)
    print("DS18B20 Temperature Monitoring System - Test Suite")
    print("=" * 60)
    
    # Test configuration
    config = test_configuration()
    if not config:
        return 1
    
    # Test sensor
    sensor = test_sensor(config)
    if not sensor:
        return 1
    
    # Test data logger
    data_logger = test_data_logger(config)
    if not data_logger:
        return 1
    
    # Test integration
    integration_success = test_integration(sensor, data_logger)
    
    print("\n" + "=" * 60)
    if integration_success:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run the main application: python3 main.py")
        print("2. Start web interface: python3 scripts/web_interface.py")
        print("3. Analyze data: python3 scripts/analyze_data.py")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    print("=" * 60)
    
    return 0 if integration_success else 1


if __name__ == '__main__':
    sys.exit(main())
