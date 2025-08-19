#!/bin/bash
# Raspberry Pi setup script

echo "Setting up Pharma Downtime Monitoring Hardware..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
sudo apt install -y python3-pip python3-venv i2c-tools

# Enable I2C and SPI
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Create virtual environment
python3 -m venv sensor_env
source sensor_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create systemd service for auto-start
sudo tee /etc/systemd/system/pharma-sensors.service > /dev/null <<EOF
[Unit]
Description=Pharma Downtime Sensor Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pharma_sensors
Environment=PATH=/home/pi/pharma_sensors/sensor_env/bin
ExecStart=/home/pi/pharma_sensors/sensor_env/bin/python sensor_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable pharma-sensors.service

echo "Setup complete! Reboot to enable I2C/SPI and start monitoring."
echo "To start manually: sudo systemctl start pharma-sensors.service"
echo "To check status: sudo systemctl status pharma-sensors.service"
echo "To view logs: sudo journalctl -u pharma-sensors.service -f"
