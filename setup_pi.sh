#!/bin/bash
# Raspberry Pi Setup Script for Pharma Downtime Monitoring
# Run this script on your Raspberry Pi to set up everything

echo "🍓 Pharma Downtime Monitoring - Raspberry Pi Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as pi user, not root"
    exit 1
fi

# Step 1: Update system
print_info "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_status "System updated"

# Step 2: Install Python and development tools
print_info "Step 2: Installing Python and development tools..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential python3-setuptools
sudo apt install -y git
print_status "Python and dev tools installed"

# Step 3: Enable hardware interfaces
print_info "Step 3: Enabling hardware interfaces..."

# Check if interfaces are already enabled
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    print_status "SPI enabled"
else
    print_status "SPI already enabled"
fi

if ! grep -q "dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    print_status "I2C enabled"
else
    print_status "I2C already enabled"
fi

if ! grep -q "dtoverlay=w1-gpio" /boot/config.txt; then
    echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
    print_status "1-Wire enabled"
else
    print_status "1-Wire already enabled"
fi

# Step 4: Install I2C tools
print_info "Step 4: Installing I2C tools..."
sudo apt install -y i2c-tools
print_status "I2C tools installed"

# Step 5: Set up project directory
print_info "Step 5: Setting up project environment..."
PROJECT_DIR="/home/pi/pharma_downtime_project"

if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found at $PROJECT_DIR"
    print_info "Please copy your project files to $PROJECT_DIR first"
    exit 1
fi

cd "$PROJECT_DIR"
print_status "Project directory found"

# Step 6: Create virtual environment
print_info "Step 6: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Step 7: Install Python packages
print_info "Step 7: Installing Python packages..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Project requirements installed"
else
    print_warning "requirements.txt not found, installing manually..."
fi

# Install Raspberry Pi specific packages
print_info "Installing Raspberry Pi sensor libraries..."
pip install RPi.GPIO
pip install adafruit-circuitpython-dht
pip install adafruit-circuitpython-ads1x15
pip install w1thermsensor
pip install board busio digitalio

# Additional packages that might be needed
pip install fastapi uvicorn websockets
pip install sqlalchemy pandas scikit-learn

print_status "All Python packages installed"

# Step 8: Set up permissions
print_info "Step 8: Setting up GPIO permissions..."
sudo usermod -a -G gpio pi
sudo usermod -a -G i2c pi
sudo usermod -a -G spi pi
print_status "User permissions configured"

# Step 9: Test hardware detection
print_info "Step 9: Testing hardware detection..."
python3 test_pi_detection.py

# Step 10: Create startup script
print_info "Step 10: Creating startup script..."
cat > start_monitoring.sh << 'EOF'
#!/bin/bash
# Pharma Downtime Monitoring Startup Script

cd /home/pi/pharma_downtime_project
source venv/bin/activate

echo "🚀 Starting Pharma Downtime Monitoring System..."
echo "📍 Project Directory: $(pwd)"
echo "🐍 Python Version: $(python3 --version)"
echo "📡 Network IP: $(hostname -I)"
echo "🌐 Dashboard will be available at: http://$(hostname -I | awk '{print $1}'):8000"
echo ""

# Run the application
python3 main.py
EOF

chmod +x start_monitoring.sh
print_status "Startup script created"

# Step 11: Final instructions
echo ""
echo "🎉 Setup Complete!"
echo "=================="
print_status "Raspberry Pi is configured for sensor monitoring"
print_warning "IMPORTANT: Reboot required for interface changes to take effect"
echo ""
echo "📋 Next Steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Connect your sensors (DHT22, DS18B20, etc.)"
echo "3. Run the application: ./start_monitoring.sh"
echo "4. Access dashboard at: http://[PI_IP]:8000"
echo ""
echo "🔧 If Pi detection fails, use: FORCE_RASPBERRY_PI=true ./start_monitoring.sh"
echo ""
print_info "Reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo reboot
fi
