#!/usr/bin/env python3
"""
Setup script for DS18B20 temperature sensor on Raspberry Pi
Enables 1-Wire interface and installs required dependencies
"""

import os
import sys
import subprocess
import logging
from pathlib import Path


def setup_logging():
    """Setup logging for setup script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def run_command(command, description, check=True):
    """Run a shell command with logging"""
    logger = logging.getLogger(__name__)
    logger.info(f"{description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Output: {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr.strip()}")
        return False


def check_raspberry_pi():
    """Check if running on Raspberry Pi"""
    logger = logging.getLogger(__name__)
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
            logger.info("Detected Raspberry Pi system")
            return True
        else:
            logger.warning("Not running on Raspberry Pi - some setup steps will be skipped")
            return False
    except FileNotFoundError:
        logger.warning("Could not detect system type - assuming non-Raspberry Pi")
        return False


def enable_1wire_interface():
    """Enable 1-Wire interface on Raspberry Pi"""
    logger = logging.getLogger(__name__)
    
    config_file = '/boot/config.txt'
    if not os.path.exists(config_file):
        config_file = '/boot/firmware/config.txt'  # For newer Pi OS versions
    
    if not os.path.exists(config_file):
        logger.error("Cannot find boot config file")
        return False
    
    # Check if 1-Wire is already enabled
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        if 'dtoverlay=w1-gpio' in content:
            logger.info("1-Wire interface already enabled")
            return True
        
        # Add 1-Wire overlay
        logger.info("Adding 1-Wire overlay to boot config...")
        with open(config_file, 'a') as f:
            f.write('\n# Enable 1-Wire interface for DS18B20\n')
            f.write('dtoverlay=w1-gpio\n')
        
        logger.info("1-Wire interface enabled. Reboot required to take effect.")
        return True
        
    except PermissionError:
        logger.error("Permission denied. Run as sudo to modify boot config.")
        return False
    except Exception as e:
        logger.error(f"Failed to enable 1-Wire interface: {e}")
        return False


def load_kernel_modules():
    """Load required kernel modules"""
    logger = logging.getLogger(__name__)
    
    modules = ['w1_gpio', 'w1_therm']
    
    for module in modules:
        if run_command(f"sudo modprobe {module}", f"Loading kernel module {module}"):
            logger.info(f"Successfully loaded {module}")
        else:
            logger.error(f"Failed to load {module}")
            return False
    
    return True


def add_modules_to_boot():
    """Add modules to load at boot"""
    logger = logging.getLogger(__name__)
    
    modules_file = '/etc/modules'
    modules = ['w1_gpio', 'w1_therm']
    
    try:
        # Read existing modules
        if os.path.exists(modules_file):
            with open(modules_file, 'r') as f:
                existing_content = f.read()
        else:
            existing_content = ''
        
        # Add modules if not already present
        modules_to_add = []
        for module in modules:
            if module not in existing_content:
                modules_to_add.append(module)
        
        if modules_to_add:
            with open(modules_file, 'a') as f:
                f.write('\n# Modules for DS18B20 temperature sensor\n')
                for module in modules_to_add:
                    f.write(f"{module}\n")
            
            logger.info(f"Added modules to boot: {', '.join(modules_to_add)}")
        else:
            logger.info("Required modules already configured for boot")
        
        return True
        
    except PermissionError:
        logger.error("Permission denied. Run as sudo to modify /etc/modules.")
        return False
    except Exception as e:
        logger.error(f"Failed to configure boot modules: {e}")
        return False


def install_python_dependencies():
    """Install required Python packages"""
    logger = logging.getLogger(__name__)
    
    packages = [
        'pandas',
        'matplotlib',
        'flask',  # For optional web interface
    ]
    
    logger.info("Installing Python dependencies...")
    
    for package in packages:
        if run_command(f"pip3 install {package}", f"Installing {package}"):
            logger.info(f"Successfully installed {package}")
        else:
            logger.warning(f"Failed to install {package}")
    
    return True


def create_directories():
    """Create required directories"""
    logger = logging.getLogger(__name__)
    
    directories = [
        'data',
        'logs',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    return True


def create_config_file():
    """Create default configuration file"""
    logger = logging.getLogger(__name__)
    
    config_content = """{
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
}"""
    
    config_file = Path('config/settings.json')
    
    if not config_file.exists():
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            f.write(config_content)
        logger.info(f"Created default configuration file: {config_file}")
    else:
        logger.info("Configuration file already exists")
    
    return True


def test_sensor_detection():
    """Test if DS18B20 sensor can be detected"""
    logger = logging.getLogger(__name__)
    
    w1_devices_dir = Path('/sys/bus/w1/devices')
    
    if not w1_devices_dir.exists():
        logger.warning("1-Wire devices directory not found. Check if modules are loaded.")
        return False
    
    # Look for DS18B20 sensors (device IDs starting with 28-)
    ds18b20_devices = list(w1_devices_dir.glob('28-*'))
    
    if ds18b20_devices:
        logger.info(f"Found {len(ds18b20_devices)} DS18B20 sensor(s):")
        for device in ds18b20_devices:
            logger.info(f"  - {device.name}")
        return True
    else:
        logger.warning("No DS18B20 sensors detected. Check wiring and connections.")
        return False


def main():
    """Main setup function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting DS18B20 temperature sensor setup...")
    
    # Check if running as root for system modifications
    is_root = os.geteuid() == 0
    is_pi = check_raspberry_pi()
    
    # Create directories and config (no root required)
    create_directories()
    create_config_file()
    
    # Install Python dependencies
    install_python_dependencies()
    
    if is_pi:
        if is_root:
            # Enable 1-Wire interface
            enable_1wire_interface()
            
            # Load kernel modules
            load_kernel_modules()
            
            # Add modules to boot configuration
            add_modules_to_boot()
            
            logger.info("System configuration complete. Reboot recommended.")
        else:
            logger.warning("Root privileges required for system configuration.")
            logger.info("Run 'sudo python3 scripts/setup_sensor.py' for full setup.")
        
        # Test sensor detection
        test_sensor_detection()
    else:
        logger.info("Non-Raspberry Pi system detected. Skipping hardware setup.")
        logger.info("Use ENABLE_MOCK_SENSOR=true for testing.")
    
    logger.info("Setup complete! You can now run the temperature monitoring:")
    logger.info("  python3 main.py")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
