# 🔌 Sensor Connection Guide for Raspberry Pi

## 📋 Hardware Requirements

### Required Sensors:
- **DS18B20** - Waterproof temperature sensor (1-Wire)
- **DHT22** - Temperature and humidity sensor
- **ADS1115** - 16-bit ADC for analog sensors
- **ADXL335** - 3-axis accelerometer (vibration)
- **ACS712** - Current sensor

### Required Components:
- 4.7kΩ resistor (for DS18B20 pull-up)
- Breadboard or PCB
- Jumper wires
- 10kΩ resistors (pull-ups for I2C if needed)

## 🔗 Wiring Connections

### DS18B20 Temperature Sensor (1-Wire)
```
DS18B20 Pin    →    Raspberry Pi
VDD (Red)      →    3.3V (Pin 1)
GND (Black)    →    GND (Pin 6)  
DQ (Yellow)    →    GPIO 4 (Pin 7)

⚡ IMPORTANT: Add 4.7kΩ resistor between VDD and DQ (pull-up resistor)
```

### DHT22 Temperature/Humidity Sensor
```
DHT22 Pin      →    Raspberry Pi
VCC (Pin 1)    →    3.3V (Pin 1)
DATA (Pin 2)   →    GPIO 18 (Pin 12)
NC (Pin 3)     →    Not connected
GND (Pin 4)    →    GND (Pin 6)

📝 Some DHT22 modules have only 3 pins (VCC, DATA, GND)
```

### ADS1115 ADC Module (I2C)
```
ADS1115 Pin    →    Raspberry Pi
VDD            →    3.3V (Pin 1)
GND            →    GND (Pin 6)
SCL            →    GPIO 3/SCL (Pin 5)
SDA            →    GPIO 2/SDA (Pin 3)
ADDR           →    GND (for 0x48 address)
```

### ADXL335 Accelerometer (Analog → ADS1115)
```
ADXL335 Pin    →    ADS1115
VCC            →    3.3V
GND            →    GND
X-OUT          →    A0 (Channel 0)
Y-OUT          →    A1 (Channel 1)
Z-OUT          →    A2 (Channel 2)
```

### ACS712 Current Sensor (Analog → ADS1115)
```
ACS712 Pin     →    ADS1115
VCC            →    5V (or 3.3V depending on module)
GND            →    GND
OUT            →    A3 (Channel 3)
```

## 🎯 GPIO Pin Reference

```
Raspberry Pi GPIO Layout (40-pin):
┌─────┬──────┬──────┬─────┐
│ 3.3V│  1 2 │ 5V   │     │
│ SDA │  3 4 │ 5V   │     │
│ SCL │  5 6 │ GND  │     │
│GPIO4│  7 8 │GPIO14│     │
│ GND │  9 10│GPIO15│     │
│     │ 11 12│GPIO18│DHT22│
│     │ 13 14│ GND  │     │
│     │ 15 16│      │     │
│     │ 17 18│      │     │
│     │ 19 20│ GND  │     │
└─────┴──────┴──────┴─────┘

Key Pins Used:
- Pin 1 (3.3V): Power for sensors
- Pin 3 (SDA): I2C data
- Pin 5 (SCL): I2C clock  
- Pin 6 (GND): Ground
- Pin 7 (GPIO4): DS18B20 data
- Pin 12 (GPIO18): DHT22 data
```

## ✅ Testing Connections

### 1. Test I2C Devices
```bash
# Should show ADS1115 at address 0x48
sudo i2cdetect -y 1
```

### 2. Test 1-Wire Devices (DS18B20)
```bash
# Should show 28-xxxxxxxxxxxx folders
ls /sys/bus/w1/devices/

# Read temperature
cat /sys/bus/w1/devices/28-*/w1_slave
```

### 3. Test GPIO Access
```bash
# Install GPIO utilities
sudo apt install wiringpi

# Check GPIO status
gpio readall
```

## 🔧 Configuration Settings

The sensors are configured in `app/core/config.py`:

```python
# GPIO pin assignments
DHT22_PIN: int = 18          # GPIO pin for DHT22
MCP3008_CHANNELS: dict = {
    "vibration_x": 0,        # ADXL335 X-axis on ADS1115 A0
    "vibration_y": 1,        # ADXL335 Y-axis on ADS1115 A1  
    "vibration_z": 2,        # ADXL335 Z-axis on ADS1115 A2
    "current": 3             # ACS712 current sensor on ADS1115 A3
}

# I2C addresses
I2C_ADDRESSES: dict = {
    "ads1115": 0x48,         # ADS1115 ADC
}
```

## 🚨 Troubleshooting

### Common Issues:

1. **"Permission denied" errors**
   ```bash
   sudo usermod -a -G gpio,i2c,spi pi
   sudo reboot
   ```

2. **I2C not working**
   ```bash
   # Enable I2C
   sudo raspi-config
   # → Interface Options → I2C → Enable
   ```

3. **1-Wire not working**
   ```bash
   # Add to /boot/config.txt
   echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
   sudo reboot
   ```

4. **Sensors not detected**
   - Check wiring connections
   - Verify power supply (3.3V vs 5V)
   - Test with multimeter
   - Check pull-up resistors

### Sensor Readings:
- **DS18B20**: Should read ~20-25°C at room temperature
- **DHT22**: Temperature ~20-25°C, Humidity ~40-60%
- **ADXL335**: Should read ~1.65V on each axis when stationary
- **ACS712**: Should read ~2.5V with no current flowing

## 📚 Next Steps

1. **Physical Setup**: Wire all sensors according to diagrams
2. **Software Test**: Run `python3 test_pi_detection.py`
3. **Hardware Test**: Run `python3 main.py` and check dashboard
4. **Calibration**: Adjust sensor thresholds in config.py as needed

Remember: Always double-check connections before powering on! 🔍
