"""
Data Logger for Temperature Monitoring
Handles data storage, CSV export, and data analysis
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class DataLogger:
    """
    Data logger for temperature sensor readings
    Supports JSON and CSV formats with data analysis capabilities
    """
    
    def __init__(self, data_file_path: str = 'data/temperature_data.json'):
        """
        Initialize data logger
        
        Args:
            data_file_path: Path to the data file
        """
        self.logger = logging.getLogger(__name__)
        self.data_file_path = Path(data_file_path)
        
        # Create data directory if it doesn't exist
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize data file if it doesn't exist
        if not self.data_file_path.exists():
            self._initialize_data_file()
    
    def _initialize_data_file(self):
        """Initialize empty data file"""
        try:
            with open(self.data_file_path, 'w') as f:
                json.dump([], f)
            self.logger.info(f"Initialized data file: {self.data_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize data file: {e}")
            raise
    
    def log_data(self, data_record: Dict):
        """
        Log temperature data record
        
        Args:
            data_record: Dictionary containing temperature data
        """
        try:
            # Load existing data
            existing_data = self._load_data()
            
            # Add new record
            existing_data.append(data_record)
            
            # Save updated data
            with open(self.data_file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            self.logger.debug(f"Logged data: {data_record}")
            
        except Exception as e:
            self.logger.error(f"Failed to log data: {e}")
    
    def _load_data(self) -> List[Dict]:
        """Load existing data from file"""
        try:
            with open(self.data_file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_recent_data(self, hours: int = 24) -> List[Dict]:
        """
        Get recent temperature data
        
        Args:
            hours: Number of hours of recent data to retrieve
            
        Returns:
            List of temperature records from the last N hours
        """
        try:
            all_data = self._load_data()
            
            if not all_data:
                return []
            
            # Filter data by time
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_data = []
            
            for record in all_data:
                try:
                    record_time = datetime.fromisoformat(record['timestamp']).timestamp()
                    if record_time >= cutoff_time:
                        recent_data.append(record)
                except (KeyError, ValueError):
                    continue
            
            return recent_data
            
        except Exception as e:
            self.logger.error(f"Failed to get recent data: {e}")
            return []
    
    def export_to_csv(self, csv_file_path: Optional[str] = None, hours: Optional[int] = None) -> str:
        """
        Export temperature data to CSV
        
        Args:
            csv_file_path: Path for CSV file (default: auto-generated)
            hours: Number of recent hours to export (default: all data)
            
        Returns:
            Path to the created CSV file
        """
        try:
            # Get data to export
            if hours:
                data = self.get_recent_data(hours)
            else:
                data = self._load_data()
            
            if not data:
                raise ValueError("No data available to export")
            
            # Generate CSV file path if not provided
            if not csv_file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_file_path = f"data/temperature_export_{timestamp}.csv"
            
            csv_path = Path(csv_file_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file
            with open(csv_path, 'w', newline='') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            self.logger.info(f"Exported {len(data)} records to {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """
        Get temperature statistics
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary containing temperature statistics
        """
        try:
            data = self.get_recent_data(hours)
            
            if not data:
                return {
                    'error': 'No data available',
                    'period_hours': hours,
                    'record_count': 0
                }
            
            temperatures = [record['temperature_celsius'] for record in data if 'temperature_celsius' in record]
            
            if not temperatures:
                return {
                    'error': 'No temperature data found',
                    'period_hours': hours,
                    'record_count': len(data)
                }
            
            stats = {
                'period_hours': hours,
                'record_count': len(temperatures),
                'min_temperature': round(min(temperatures), 2),
                'max_temperature': round(max(temperatures), 2),
                'avg_temperature': round(sum(temperatures) / len(temperatures), 2),
                'first_reading': data[0]['timestamp'] if data else None,
                'last_reading': data[-1]['timestamp'] if data else None
            }
            
            # Calculate median
            sorted_temps = sorted(temperatures)
            n = len(sorted_temps)
            if n % 2 == 0:
                stats['median_temperature'] = round((sorted_temps[n//2-1] + sorted_temps[n//2]) / 2, 2)
            else:
                stats['median_temperature'] = round(sorted_temps[n//2], 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate statistics: {e}")
            return {
                'error': str(e),
                'period_hours': hours,
                'record_count': 0
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Remove old data records
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            all_data = self._load_data()
            
            if not all_data:
                return
            
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            filtered_data = []
            removed_count = 0
            
            for record in all_data:
                try:
                    record_time = datetime.fromisoformat(record['timestamp']).timestamp()
                    if record_time >= cutoff_time:
                        filtered_data.append(record)
                    else:
                        removed_count += 1
                except (KeyError, ValueError):
                    # Keep records with invalid timestamps
                    filtered_data.append(record)
            
            if removed_count > 0:
                # Save cleaned data
                with open(self.data_file_path, 'w') as f:
                    json.dump(filtered_data, f, indent=2)
                
                self.logger.info(f"Cleaned up {removed_count} old records, kept {len(filtered_data)} records")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def get_data_file_info(self) -> Dict:
        """Get information about the data file"""
        try:
            if not self.data_file_path.exists():
                return {
                    'file_exists': False,
                    'file_path': str(self.data_file_path)
                }
            
            data = self._load_data()
            file_size = self.data_file_path.stat().st_size
            
            return {
                'file_exists': True,
                'file_path': str(self.data_file_path),
                'file_size_bytes': file_size,
                'record_count': len(data),
                'last_modified': datetime.fromtimestamp(
                    self.data_file_path.stat().st_mtime
                ).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get data file info: {e}")
            return {
                'error': str(e),
                'file_path': str(self.data_file_path)
            }
