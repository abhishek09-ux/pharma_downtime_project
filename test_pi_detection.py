#!/usr/bin/env python3
"""
Test script to verify Raspberry Pi detection methods
Run this on your Raspberry Pi to check if detection is working
"""
import os
import platform

def test_pi_detection():
    print("🔍 Testing Raspberry Pi Detection Methods...")
    print(f"🖥️ Platform: {platform.platform()}")
    print(f"🖥️ Machine: {platform.machine()}")
    print(f"🖥️ System: {platform.system()}")
    print("-" * 50)
    
    detected = False
    
    # Test 1: Device tree model
    print("📱 Method 1: Checking /proc/device-tree/model")
    if os.path.exists('/proc/device-tree/model'):
        try:
            with open('/proc/device-tree/model', 'rb') as f:
                model = f.read().decode('utf-8', errors='ignore').strip('\x00')
                print(f"   Device Model: {model}")
                if 'Raspberry Pi' in model:
                    print("   ✅ SUCCESS: Device tree detection found Raspberry Pi")
                    detected = True
                else:
                    print("   ❌ Device tree exists but doesn't contain 'Raspberry Pi'")
        except Exception as e:
            print(f"   ❌ Error reading device tree: {e}")
    else:
        print("   ❌ /proc/device-tree/model not found")
    
    print()
    
    # Test 2: cpuinfo
    print("🖥️ Method 2: Checking /proc/cpuinfo")
    if os.path.exists('/proc/cpuinfo'):
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                
            # Check for various Pi identifiers
            identifiers = {
                'bcm2': 'bcm2' in cpuinfo,
                'raspberry': 'raspberry' in cpuinfo,
                'arm': 'arm' in cpuinfo,
                'hardware': any(hw in cpuinfo for hw in ['bcm2708', 'bcm2709', 'bcm2710', 'bcm2711'])
            }
            
            for identifier, found in identifiers.items():
                status = "✅" if found else "❌"
                print(f"   {status} Contains '{identifier}': {found}")
                if found:
                    detected = True
                    
        except Exception as e:
            print(f"   ❌ Error reading cpuinfo: {e}")
    else:
        print("   ❌ /proc/cpuinfo not found")
    
    print()
    
    # Test 3: Pi directories
    print("📁 Method 3: Checking Pi-specific directories")
    pi_dirs = ['/sys/firmware/devicetree/base', '/opt/vc', '/boot/config.txt']
    for d in pi_dirs:
        exists = os.path.exists(d)
        status = "✅" if exists else "❌"
        print(f"   {status} {d}: {'Found' if exists else 'Not found'}")
        if exists:
            detected = True
    
    print()
    print("-" * 50)
    
    if detected:
        print("🎉 SUCCESS: Raspberry Pi detected!")
        print("💡 Your Pi detection should work automatically")
    else:
        print("⚠️  WARNING: Raspberry Pi not detected")
        print("💡 You may need to use FORCE_RASPBERRY_PI=true")
        print("💡 Or check if you're running on actual Pi hardware")
    
    return detected

def test_sensor_interfaces():
    print("\n🔌 Testing Sensor Interface Availability...")
    print("-" * 50)
    
    # Check GPIO
    gpio_paths = ['/sys/class/gpio', '/dev/gpiomem']
    for path in gpio_paths:
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"   {status} GPIO interface ({path}): {'Available' if exists else 'Not available'}")
    
    # Check I2C
    i2c_devices = ['/dev/i2c-1', '/dev/i2c-0']
    for device in i2c_devices:
        exists = os.path.exists(device)
        status = "✅" if exists else "❌"
        print(f"   {status} I2C interface ({device}): {'Available' if exists else 'Not available'}")
    
    # Check SPI
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
    for device in spi_devices:
        exists = os.path.exists(device)
        status = "✅" if exists else "❌"
        print(f"   {status} SPI interface ({device}): {'Available' if exists else 'Not available'}")
    
    # Check 1-Wire
    w1_path = '/sys/bus/w1/devices'
    if os.path.exists(w1_path):
        devices = os.listdir(w1_path)
        print(f"   ✅ 1-Wire interface: Available")
        print(f"   📱 1-Wire devices found: {len(devices)}")
        for device in devices:
            if device.startswith('28-'):  # DS18B20 family
                print(f"      🌡️ DS18B20 Temperature sensor: {device}")
    else:
        print(f"   ❌ 1-Wire interface: Not available")

if __name__ == "__main__":
    print("🔬 Raspberry Pi Hardware Detection Test")
    print("=" * 60)
    
    # Test Pi detection
    pi_detected = test_pi_detection()
    
    # Test sensor interfaces
    test_sensor_interfaces()
    
    print("\n" + "=" * 60)
    if pi_detected:
        print("🚀 READY: You can run 'python3 main.py' directly")
    else:
        print("🔧 ALTERNATIVE: Use 'FORCE_RASPBERRY_PI=true python3 main.py'")
    print("📋 Copy this output and let me know what you see!")
