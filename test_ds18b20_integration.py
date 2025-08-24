#!/usr/bin/env python3
"""
Raspberry Pi DS18B20 Test Script for Pharma Downtime Project
This script tests ONLY the DS18B20 sensor integration in your main project
"""

import sys
import os
import logging
from datetime import datetime

# Add temperature_detection to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'temperature_detection', 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ds18b20_test")

def test_terminal_sensor():
    """Test DS18B20 directly from terminal like you did"""
    print("=" * 60)
    print("🔍 Testing DS18B20 from Terminal (Direct)")
    print("=" * 60)
    
    try:
        import glob
        
        # Check for 1-Wire devices
        device_folders = glob.glob('/sys/bus/w1/devices/28*')
        if not device_folders:
            print("❌ No DS18B20 sensors found in /sys/bus/w1/devices/")
            return False
            
        print(f"✅ Found {len(device_folders)} DS18B20 sensor(s):")
        
        for device_folder in device_folders:
            sensor_id = device_folder.split('/')[-1]
            device_file = f"{device_folder}/w1_slave"
            
            try:
                with open(device_file, 'r') as f:
                    lines = f.readlines()
                
                # Check CRC
                if lines[0].strip()[-3:] != 'YES':
                    print(f"⚠️  {sensor_id}: CRC check failed")
                    continue
                
                # Extract temperature
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    temp_f = (temp_c * 9/5) + 32
                    print(f"🌡️  {sensor_id}: {temp_c:.2f}°C ({temp_f:.2f}°F)")
                else:
                    print(f"❌ {sensor_id}: Could not parse temperature")
                    
            except Exception as e:
                print(f"❌ {sensor_id}: Error reading - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Terminal test failed: {e}")
        return False

def test_project_ds18b20_module():
    """Test DS18B20 using your project's temperature_detection module"""
    print("\n" + "=" * 60)
    print("🔍 Testing DS18B20 via Project Module")
    print("=" * 60)
    
    try:
        from sensor.ds18b20_reader import DS18B20Reader, MockDS18B20Reader
        
        # Try real sensor
        try:
            sensor = DS18B20Reader()
            print("✅ DS18B20Reader initialized successfully")
            
            # Test sensor info
            info = sensor.get_sensor_info()
            print(f"📱 Sensor Info:")
            print(f"   - ID: {info['sensor_id']}")
            print(f"   - Type: {info['sensor_type']}")
            print(f"   - Interface: {info['interface']}")
            
            # Test connection
            connected = sensor.is_connected()
            print(f"   - Connected: {'✅ YES' if connected else '❌ NO'}")
            
            if connected:
                # Test temperature reading
                for i in range(3):
                    temp = sensor.read_temperature()
                    if temp is not None:
                        temp_f = (temp * 9/5) + 32
                        print(f"🌡️  Reading {i+1}: {temp:.2f}°C ({temp_f:.2f}°F)")
                    else:
                        print(f"❌ Reading {i+1}: Failed")
                return True
            else:
                print("❌ Sensor not connected")
                return False
                
        except Exception as e:
            print(f"❌ DS18B20Reader failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure temperature_detection is properly integrated")
        return False

def test_project_raspberry_pi_detection():
    """Test Raspberry Pi detection from your main project"""
    print("\n" + "=" * 60)
    print("🔍 Testing Raspberry Pi Detection")
    print("=" * 60)
    
    # Add project root to path
    project_root = os.path.dirname(__file__)
    sys.path.insert(0, project_root)
    
    try:
        from app.core.config import settings
        
        print(f"🖥️  Raspberry Pi Mode: {'✅ TRUE' if settings.RASPBERRY_PI_MODE else '❌ FALSE'}")
        
        # Manual detection tests
        tests = {
            '/proc/device-tree/model': 'Device Tree Model',
            '/proc/cpuinfo': 'CPU Info',
            '/sys/firmware/devicetree/base': 'Device Tree Base',
            '/opt/vc': 'VideoCore'
        }
        
        for path, name in tests.items():
            exists = os.path.exists(path)
            print(f"📁 {name}: {'✅ Found' if exists else '❌ Not Found'} ({path})")
        
        return settings.RASPBERRY_PI_MODE
        
    except Exception as e:
        print(f"❌ Pi detection test failed: {e}")
        return False

def test_main_project_integration():
    """Test how your main project handles DS18B20"""
    print("\n" + "=" * 60)
    print("🔍 Testing Main Project DS18B20 Integration")
    print("=" * 60)
    
    try:
        # Import from your main project
        project_root = os.path.dirname(__file__)
        sys.path.insert(0, project_root)
        
        # Check DS18B20 availability flag
        print("📦 Checking DS18B20 module availability...")
        
        try:
            from sensor.ds18b20_reader import DS18B20Reader, MockDS18B20Reader
            print("✅ DS18B20 modules imported successfully")
            
            # Simulate main.py initialization logic
            print("\n🔧 Simulating main.py initialization...")
            
            from app.core.config import settings
            RASPBERRY_PI = settings.RASPBERRY_PI_MODE
            FORCE_PI_MODE = os.getenv("FORCE_RASPBERRY_PI", "false").lower() == "true"
            
            print(f"   - RASPBERRY_PI: {RASPBERRY_PI}")
            print(f"   - FORCE_PI_MODE: {FORCE_PI_MODE}")
            
            ds18b20_sensor = None
            
            if RASPBERRY_PI and not FORCE_PI_MODE:
                try:
                    ds18b20_sensor = DS18B20Reader()
                    print("✅ DS18B20 initialized in REAL mode")
                except Exception as e:
                    print(f"❌ DS18B20 initialization failed: {e}")
            elif FORCE_PI_MODE:
                ds18b20_sensor = MockDS18B20Reader()
                print("⚠️  DS18B20 initialized in MOCK mode")
            else:
                print("❌ DS18B20 not initialized (simulation mode)")
            
            if ds18b20_sensor:
                # Test reading
                temp = ds18b20_sensor.read_temperature()
                if temp is not None:
                    print(f"🌡️  Temperature reading: {temp:.2f}°C")
                    return True
                else:
                    print("❌ Failed to read temperature")
                    return False
            else:
                print("❌ No DS18B20 sensor available")
                return False
                
        except ImportError as e:
            print(f"❌ DS18B20 module import failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Main project integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 DS18B20 Integration Test Suite for Pharma Downtime Project")
    print("=" * 70)
    
    results = {
        "Terminal DS18B20": test_terminal_sensor(),
        "Project DS18B20 Module": test_project_ds18b20_module(),
        "Raspberry Pi Detection": test_project_raspberry_pi_detection(),
        "Main Project Integration": test_main_project_integration()
    }
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your DS18B20 integration should work!")
        print("\n📋 Next Steps:")
        print("1. Run your main application: python3 main.py")
        print("2. Check that DS18B20 shows 'online' status")
        print("3. Verify real temperature readings in dashboard")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\n🔧 Troubleshooting:")
        if not results["Terminal DS18B20"]:
            print("- Check DS18B20 wiring and 1-Wire configuration")
        if not results["Raspberry Pi Detection"]:
            print("- Use FORCE_RASPBERRY_PI=true if needed")
        if not results["Project DS18B20 Module"]:
            print("- Check temperature_detection integration")
        if not results["Main Project Integration"]:
            print("- Check main.py DS18B20 initialization logic")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
