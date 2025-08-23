# DS18B20 Temperature Monitoring System

A comprehensive Python project for real-time temperature monitoring using the DS18B20 temperature sensor connected to a Raspberry Pi.

## Features

- **Real-time Temperature Monitoring**: Continuous temperature readings from DS18B20 sensor
- **Data Logging**: Automatic data storage in JSON format with CSV export capability
- **Temperature Alerts**: Configurable high/low temperature thresholds
- **Data Analysis**: Statistical analysis and visualization tools
- **Web Interface**: Optional web-based dashboard for remote monitoring
- **Mock Sensor Support**: Testing capability on non-Raspberry Pi systems
- **Configurable Settings**: Flexible configuration via JSON files and environment variables

## Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- DS18B20 temperature sensor
- 4.7kΩ resistor (pull-up resistor)
- Connecting wires
- Breadboard (optional)

## Wiring Diagram

```
DS18B20 Sensor Wiring:
┌─────────────┐
│  DS18B20    │
│             │
│ VCC  ●───────● 3.3V (Pin 1)
│             │
│ DATA ●───────● GPIO 4 (Pin 7)
│      │      │
│      └──[4.7kΩ]──● 3.3V (Pin 1)
│             │
│ GND  ●───────● Ground (Pin 6)
└─────────────┘
```

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd temperature_detection
```

### 2. Run the Setup Script

On Raspberry Pi:
```bash
# For full system setup (requires sudo)
sudo python3 scripts/setup_sensor.py

# For user-level setup only
python3 scripts/setup_sensor.py
```

On other systems (for testing):
```bash
python3 scripts/setup_sensor.py
```

### 3. Manual Installation (Alternative)

If you prefer manual installation:

```bash
# Install Python dependencies
pip3 install pandas matplotlib flask

# On Raspberry Pi, enable 1-Wire interface
sudo raspi-config
# Navigate to: Interfacing Options > 1-Wire > Enable

# Load kernel modules
sudo modprobe w1-gpio
sudo modprobe w1-therm

# Add modules to /etc/modules for permanent loading
echo 'w1-gpio' | sudo tee -a /etc/modules
echo 'w1-therm' | sudo tee -a /etc/modules
```

## Configuration

### Configuration File

Create or edit `config/settings.json`:

```json
{
  "SENSOR_ID": null,
  "READ_INTERVAL": 2.0,
  "DATA_FILE_PATH": "data/temperature_data.json",
  "ENABLE_ALERTS": true,
  "HIGH_TEMP_THRESHOLD": 30.0,
  "LOW_TEMP_THRESHOLD": 0.0,
  "LOG_LEVEL": "INFO",
  "DATA_RETENTION_DAYS": 30,
  "ENABLE_WEB_SERVER": false,
  "WEB_SERVER_PORT": 8080,
  "ENABLE_MOCK_SENSOR": false
}
```

### Environment Variables

You can also configure using environment variables:

```bash
export SENSOR_ID="28-0000012345678"
export READ_INTERVAL=1.0
export HIGH_TEMP_THRESHOLD=35.0
export ENABLE_ALERTS=true
```

## Usage

### Basic Temperature Monitoring

Start the main temperature monitoring application:

```bash
python3 main.py
```

This will:
- Initialize the DS18B20 sensor
- Start continuous temperature readings
- Log data to JSON file
- Display real-time temperature in console
- Check for temperature alerts

### Web Interface

To enable the web interface, set `ENABLE_WEB_SERVER=true` in configuration or:

```bash
python3 scripts/web_interface.py
```

Access the web interface at: `http://localhost:8080`

### Data Analysis

Analyze collected temperature data:

```bash
# Analyze last 24 hours (default)
python3 scripts/analyze_data.py

# Analyze last 6 hours
python3 scripts/analyze_data.py --hours 6

# Analyze all data
python3 scripts/analyze_data.py --hours 0

# Generate charts and save to custom directory
python3 scripts/analyze_data.py --output-dir reports

# Show statistics only (no file output)
python3 scripts/analyze_data.py --stats-only
```

## Project Structure

```
temperature_detection/
├── main.py                 # Main application entry point
├── src/                    # Source code modules
│   ├── sensor/             # Sensor handling
│   │   ├── ds18b20_reader.py
│   │   └── __init__.py
│   ├── data/               # Data management
│   │   ├── data_logger.py
│   │   └── __init__.py
│   ├── config/             # Configuration management
│   │   ├── settings.py
│   │   └── __init__.py
│   └── __init__.py
├── scripts/                # Utility scripts
│   ├── setup_sensor.py     # Setup and configuration
│   ├── analyze_data.py     # Data analysis and visualization
│   └── web_interface.py    # Web dashboard
├── data/                   # Data storage directory
├── logs/                   # Log files directory
├── config/                 # Configuration files
├── templates/              # Web interface templates
└── README.md
```

## API Reference

### DS18B20Reader Class

```python
from src.sensor.ds18b20_reader import DS18B20Reader

# Initialize sensor
sensor = DS18B20Reader(sensor_id="28-0000012345678")

# Read temperature
temperature = sensor.read_temperature()  # Returns float in Celsius

# Get sensor info
info = sensor.get_sensor_info()

# Check connection
is_connected = sensor.is_connected()
```

### DataLogger Class

```python
from src.data.data_logger import DataLogger

# Initialize logger
logger = DataLogger("data/temperature_data.json")

# Log temperature data
data_record = {
    'timestamp': datetime.now().isoformat(),
    'temperature_celsius': 22.5,
    'temperature_fahrenheit': 72.5,
    'sensor_id': '28-0000012345678'
}
logger.log_data(data_record)

# Get recent data
recent_data = logger.get_recent_data(hours=24)

# Export to CSV
csv_file = logger.export_to_csv()

# Get statistics
stats = logger.get_statistics(hours=24)
```

## Troubleshooting

### Sensor Not Detected

1. Check wiring connections
2. Verify 1-Wire interface is enabled:
   ```bash
   ls /sys/bus/w1/devices/
   ```
3. Check for DS18B20 devices:
   ```bash
   ls /sys/bus/w1/devices/28*
   ```

### Permission Errors

Run setup script with sudo privileges:
```bash
sudo python3 scripts/setup_sensor.py
```

### Testing Without Hardware

Enable mock sensor for testing:
```bash
export ENABLE_MOCK_SENSOR=true
python3 main.py
```

### Module Import Errors

Ensure you're running from the project root directory:
```bash
cd temperature_detection
python3 main.py
```

## Temperature Sensor Information

### DS18B20 Specifications

- **Operating Voltage**: 3.0V to 5.5V
- **Temperature Range**: -55°C to +125°C
- **Accuracy**: ±0.5°C (from -10°C to +85°C)
- **Resolution**: 9 to 12 bits (configurable)
- **Interface**: 1-Wire protocol
- **Conversion Time**: 750ms (12-bit)

### 1-Wire Protocol

The DS18B20 uses the 1-Wire protocol, which allows multiple sensors on a single data line. Each sensor has a unique 64-bit serial code for identification.

## Advanced Features

### Multiple Sensors

To use multiple DS18B20 sensors:

1. Connect all sensors to the same GPIO pin
2. List available sensors:
   ```bash
   ls /sys/bus/w1/devices/28*
   ```
3. Specify sensor ID in configuration or code

### Automatic Data Cleanup

Configure automatic cleanup of old data:
```python
# Clean up data older than 30 days
logger.cleanup_old_data(days_to_keep=30)
```

### Custom Alerts

Implement custom alert handling:
```python
def custom_alert_handler(temperature, threshold_type):
    # Send email, SMS, or other notification
    pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in the `logs/` directory
3. Create an issue in the repository

## Changelog

### Version 1.0.0
- Initial release
- Basic DS18B20 temperature monitoring
- Data logging and analysis
- Web interface
- Configuration management
- Mock sensor support for testing
