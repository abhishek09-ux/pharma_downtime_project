#!/usr/bin/env python3
"""
Simple web interface for temperature monitoring
Provides real-time temperature display and basic charts
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import threading
import time

# Import our temperature monitoring components
import sys
sys.path.append('..')
from src.sensor.ds18b20_reader import DS18B20Reader, MockDS18B20Reader
from src.data.data_logger import DataLogger
from src.config.settings import Config


app = Flask(__name__)
app.config['SECRET_KEY'] = 'temperature-monitor-secret-key'

# Global variables
temperature_reader = None
data_logger = None
config = None
latest_reading = None


def initialize_components():
    """Initialize temperature monitoring components"""
    global temperature_reader, data_logger, config
    
    config = Config()
    
    # Initialize sensor (mock if not on Pi or if enabled)
    if config.ENABLE_MOCK_SENSOR:
        temperature_reader = MockDS18B20Reader()
    else:
        try:
            temperature_reader = DS18B20Reader(sensor_id=config.SENSOR_ID)
        except Exception:
            logging.warning("Failed to initialize real sensor, using mock sensor")
            temperature_reader = MockDS18B20Reader()
    
    # Initialize data logger
    data_logger = DataLogger(config.DATA_FILE_PATH)


def background_monitoring():
    """Background thread for continuous temperature monitoring"""
    global latest_reading
    
    while True:
        try:
            if temperature_reader:
                temp = temperature_reader.read_temperature()
                if temp is not None:
                    latest_reading = {
                        'timestamp': datetime.now().isoformat(),
                        'temperature_celsius': round(temp, 2),
                        'temperature_fahrenheit': round((temp * 9/5) + 32, 2),
                        'sensor_id': getattr(temperature_reader, 'sensor_id', 'unknown')
                    }
                    
                    # Log data
                    if data_logger:
                        data_logger.log_data(latest_reading)
            
            time.sleep(config.READ_INTERVAL if config else 5)
            
        except Exception as e:
            logging.error(f"Error in background monitoring: {e}")
            time.sleep(10)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/current')
def api_current():
    """Get current temperature reading"""
    if latest_reading:
        return jsonify(latest_reading)
    else:
        return jsonify({'error': 'No temperature data available'}), 404


@app.route('/api/history')
def api_history():
    """Get historical temperature data"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if data_logger:
            data = data_logger.get_recent_data(hours)
            return jsonify(data)
        else:
            return jsonify({'error': 'Data logger not available'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics')
def api_statistics():
    """Get temperature statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if data_logger:
            stats = data_logger.get_statistics(hours)
            return jsonify(stats)
        else:
            return jsonify({'error': 'Data logger not available'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensor-info')
def api_sensor_info():
    """Get sensor information"""
    if temperature_reader:
        info = temperature_reader.get_sensor_info()
        info['connected'] = temperature_reader.is_connected()
        return jsonify(info)
    else:
        return jsonify({'error': 'Sensor not available'}), 500


# HTML template for the web interface
def create_html_template():
    """Create HTML template file"""
    template_dir = Path('templates')
    template_dir.mkdir(exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temperature Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .current-temp {
            background: white;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .temp-value {
            font-size: 3em;
            font-weight: bold;
            color: #2c3e50;
        }
        .temp-unit {
            font-size: 1.2em;
            color: #7f8c8d;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #34495e;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .controls {
            text-align: center;
            margin-bottom: 20px;
        }
        select, button {
            padding: 10px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            background-color: #3498db;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #2980b9;
        }
        .status {
            text-align: center;
            margin: 10px 0;
        }
        .error {
            color: #e74c3c;
        }
        .success {
            color: #27ae60;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌡️ Temperature Monitor</h1>
            <div id="status" class="status"></div>
        </div>

        <div class="current-temp" id="currentTemp">
            <div class="temp-value">--</div>
            <div class="temp-unit">°C</div>
            <div style="margin-top: 10px; color: #7f8c8d;">
                <span id="lastUpdate">No data</span>
            </div>
        </div>

        <div class="stats-grid" id="statsGrid">
            <!-- Statistics will be populated here -->
        </div>

        <div class="controls">
            <select id="timeRange">
                <option value="1">Last 1 hour</option>
                <option value="6">Last 6 hours</option>
                <option value="24" selected>Last 24 hours</option>
                <option value="168">Last week</option>
            </select>
            <button onclick="updateData()">Refresh</button>
            <button onclick="exportData()">Export CSV</button>
        </div>

        <div class="chart-container">
            <canvas id="temperatureChart"></canvas>
        </div>
    </div>

    <script>
        let chart = null;
        
        function updateCurrentTemp() {
            fetch('/api/current')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('status').innerHTML = 
                            `<span class="error">Error: ${data.error}</span>`;
                        return;
                    }
                    
                    const tempElement = document.querySelector('.temp-value');
                    tempElement.textContent = data.temperature_celsius;
                    
                    const updateElement = document.getElementById('lastUpdate');
                    const timestamp = new Date(data.timestamp);
                    updateElement.textContent = `Last update: ${timestamp.toLocaleTimeString()}`;
                    
                    document.getElementById('status').innerHTML = 
                        `<span class="success">✓ Connected to sensor ${data.sensor_id}</span>`;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = 
                        `<span class="error">Connection error: ${error.message}</span>`;
                });
        }
        
        function updateStatistics() {
            const hours = document.getElementById('timeRange').value;
            
            fetch(`/api/statistics?hours=${hours}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) return;
                    
                    const statsGrid = document.getElementById('statsGrid');
                    statsGrid.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${data.min_temperature || '--'}</div>
                            <div class="stat-label">Min Temperature (°C)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.max_temperature || '--'}</div>
                            <div class="stat-label">Max Temperature (°C)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.avg_temperature || '--'}</div>
                            <div class="stat-label">Average Temperature (°C)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.record_count || 0}</div>
                            <div class="stat-label">Readings</div>
                        </div>
                    `;
                });
        }
        
        function updateChart() {
            const hours = document.getElementById('timeRange').value;
            
            fetch(`/api/history?hours=${hours}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error || !data.length) return;
                    
                    const labels = data.map(item => new Date(item.timestamp).toLocaleTimeString());
                    const temperatures = data.map(item => item.temperature_celsius);
                    
                    if (chart) {
                        chart.destroy();
                    }
                    
                    const ctx = document.getElementById('temperatureChart').getContext('2d');
                    chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Temperature (°C)',
                                data: temperatures,
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: false,
                                    title: {
                                        display: true,
                                        text: 'Temperature (°C)'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Time'
                                    }
                                }
                            }
                        }
                    });
                });
        }
        
        function updateData() {
            updateCurrentTemp();
            updateStatistics();
            updateChart();
        }
        
        function exportData() {
            const hours = document.getElementById('timeRange').value;
            window.location.href = `/api/history?hours=${hours}&format=csv`;
        }
        
        // Update data on page load
        updateData();
        
        // Auto-refresh every 30 seconds
        setInterval(updateCurrentTemp, 30000);
        
        // Update charts when time range changes
        document.getElementById('timeRange').addEventListener('change', function() {
            updateStatistics();
            updateChart();
        });
    </script>
</body>
</html>'''
    
    with open(template_dir / 'index.html', 'w') as f:
        f.write(html_content)


def main():
    """Main web server function"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        initialize_components()
        
        # Create HTML template
        create_html_template()
        
        # Start background monitoring thread
        monitor_thread = threading.Thread(target=background_monitoring, daemon=True)
        monitor_thread.start()
        
        # Start web server
        port = config.WEB_SERVER_PORT if config else 8080
        logger.info(f"Starting web server on http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
