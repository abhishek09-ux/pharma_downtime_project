"""
Configuration settings for temperature monitoring system
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional


class Config:
    """
    Configuration management for temperature monitoring system
    Supports environment variables and JSON config files
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to JSON configuration file (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration values
        self._defaults = {
            'SENSOR_ID': None,  # Auto-detect if None
            'READ_INTERVAL': 2.0,  # seconds
            'DATA_FILE_PATH': 'data/temperature_data.json',
            'ENABLE_ALERTS': True,
            'HIGH_TEMP_THRESHOLD': 30.0,  # Celsius
            'LOW_TEMP_THRESHOLD': 0.0,    # Celsius
            'LOG_LEVEL': 'INFO',
            'DATA_RETENTION_DAYS': 30,
            'ENABLE_WEB_SERVER': False,
            'WEB_SERVER_PORT': 8080,
            'ENABLE_MOCK_SENSOR': False  # For testing on non-Pi systems
        }
        
        # Load configuration
        self._load_config(config_file)
    
    def _load_config(self, config_file: Optional[str]):
        """Load configuration from file and environment variables"""
        config = self._defaults.copy()
        
        # Load from JSON file if provided
        if config_file:
            config.update(self._load_from_file(config_file))
        
        # Load from environment variables (highest priority)
        config.update(self._load_from_env())
        
        # Set attributes
        for key, value in config.items():
            setattr(self, key, value)
        
        self.logger.info("Configuration loaded successfully")
    
    def _load_from_file(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                self.logger.info(f"Loaded configuration from {config_file}")
                return file_config
            else:
                self.logger.warning(f"Configuration file not found: {config_file}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load configuration file {config_file}: {e}")
            return {}
    
    def _load_from_env(self) -> dict:
        """Load configuration from environment variables"""
        env_config = {}
        
        for key in self._defaults.keys():
            env_value = os.getenv(key)
            if env_value is not None:
                # Convert string values to appropriate types
                env_config[key] = self._convert_env_value(key, env_value)
        
        if env_config:
            self.logger.info(f"Loaded {len(env_config)} settings from environment variables")
        
        return env_config
    
    def _convert_env_value(self, key: str, value: str):
        """Convert environment variable string to appropriate type"""
        try:
            # Boolean values
            if key in ['ENABLE_ALERTS', 'ENABLE_WEB_SERVER', 'ENABLE_MOCK_SENSOR']:
                return value.lower() in ('true', '1', 'yes', 'on')
            
            # Integer values
            if key in ['WEB_SERVER_PORT', 'DATA_RETENTION_DAYS']:
                return int(value)
            
            # Float values
            if key in ['READ_INTERVAL', 'HIGH_TEMP_THRESHOLD', 'LOW_TEMP_THRESHOLD']:
                return float(value)
            
            # String values (default)
            return value
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to convert environment variable {key}={value}: {e}")
            return self._defaults.get(key)
    
    def save_to_file(self, config_file: str):
        """Save current configuration to JSON file"""
        try:
            config_data = {}
            for key in self._defaults.keys():
                config_data[key] = getattr(self, key)
            
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {config_file}: {e}")
    
    def get_config_dict(self) -> dict:
        """Get configuration as dictionary"""
        return {key: getattr(self, key) for key in self._defaults.keys()}
    
    def update_config(self, **kwargs):
        """Update configuration values"""
        for key, value in kwargs.items():
            if key in self._defaults:
                setattr(self, key, value)
                self.logger.info(f"Updated configuration: {key} = {value}")
            else:
                self.logger.warning(f"Unknown configuration key: {key}")
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        valid = True
        
        # Validate temperature thresholds
        if self.HIGH_TEMP_THRESHOLD <= self.LOW_TEMP_THRESHOLD:
            self.logger.error("HIGH_TEMP_THRESHOLD must be greater than LOW_TEMP_THRESHOLD")
            valid = False
        
        # Validate read interval
        if self.READ_INTERVAL <= 0:
            self.logger.error("READ_INTERVAL must be positive")
            valid = False
        
        # Validate port number
        if not (1024 <= self.WEB_SERVER_PORT <= 65535):
            self.logger.error("WEB_SERVER_PORT must be between 1024 and 65535")
            valid = False
        
        # Validate data retention
        if self.DATA_RETENTION_DAYS <= 0:
            self.logger.error("DATA_RETENTION_DAYS must be positive")
            valid = False
        
        return valid
    
    def __str__(self) -> str:
        """String representation of configuration"""
        config_items = []
        for key in sorted(self._defaults.keys()):
            value = getattr(self, key)
            # Hide sensitive information if any
            config_items.append(f"{key}: {value}")
        
        return "Configuration:\n" + "\n".join(f"  {item}" for item in config_items)
