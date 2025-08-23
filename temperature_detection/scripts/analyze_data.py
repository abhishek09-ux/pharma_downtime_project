#!/usr/bin/env python3
"""
Data analysis and visualization script for temperature monitoring
Generates charts and statistics from collected temperature data
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def load_temperature_data(data_file: str) -> pd.DataFrame:
    """Load temperature data into pandas DataFrame"""
    logger = logging.getLogger(__name__)
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            raise ValueError("No data found in file")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        logger.info(f"Loaded {len(df)} temperature records")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load temperature data: {e}")
        raise


def generate_temperature_chart(df: pd.DataFrame, output_file: str, hours: int = 24):
    """Generate temperature vs time chart"""
    logger = logging.getLogger(__name__)
    
    # Filter data for specified time period
    if hours > 0:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        df_filtered = df[df.index >= cutoff_time]
    else:
        df_filtered = df
    
    if df_filtered.empty:
        logger.warning("No data available for the specified time period")
        return
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Plot temperature
    plt.subplot(2, 1, 1)
    plt.plot(df_filtered.index, df_filtered['temperature_celsius'], 
             'b-', linewidth=1, label='Temperature (°C)')
    plt.title(f'Temperature Monitoring - Last {hours} Hours' if hours > 0 else 'Temperature Monitoring - All Data')
    plt.ylabel('Temperature (°C)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//12)))
    plt.xticks(rotation=45)
    
    # Plot temperature in Fahrenheit
    plt.subplot(2, 1, 2)
    plt.plot(df_filtered.index, df_filtered['temperature_fahrenheit'], 
             'r-', linewidth=1, label='Temperature (°F)')
    plt.ylabel('Temperature (°F)')
    plt.xlabel('Time')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//12)))
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save chart
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Temperature chart saved: {output_file}")


def generate_statistics_report(df: pd.DataFrame, hours: int = 24) -> dict:
    """Generate detailed statistics report"""
    logger = logging.getLogger(__name__)
    
    # Filter data for specified time period
    if hours > 0:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        df_filtered = df[df.index >= cutoff_time]
    else:
        df_filtered = df
    
    if df_filtered.empty:
        logger.warning("No data available for statistics")
        return {}
    
    temp_c = df_filtered['temperature_celsius']
    temp_f = df_filtered['temperature_fahrenheit']
    
    stats = {
        'period': f"Last {hours} hours" if hours > 0 else "All data",
        'record_count': len(df_filtered),
        'time_range': {
            'start': df_filtered.index.min().isoformat(),
            'end': df_filtered.index.max().isoformat(),
            'duration_hours': (df_filtered.index.max() - df_filtered.index.min()).total_seconds() / 3600
        },
        'celsius': {
            'min': round(temp_c.min(), 2),
            'max': round(temp_c.max(), 2),
            'mean': round(temp_c.mean(), 2),
            'median': round(temp_c.median(), 2),
            'std': round(temp_c.std(), 2)
        },
        'fahrenheit': {
            'min': round(temp_f.min(), 2),
            'max': round(temp_f.max(), 2),
            'mean': round(temp_f.mean(), 2),
            'median': round(temp_f.median(), 2),
            'std': round(temp_f.std(), 2)
        }
    }
    
    # Calculate temperature trends
    if len(df_filtered) > 1:
        # Linear trend (slope per hour)
        time_hours = (df_filtered.index - df_filtered.index[0]).total_seconds() / 3600
        slope = pd.Series(time_hours).corr(temp_c) * temp_c.std() / pd.Series(time_hours).std()
        stats['trend'] = {
            'slope_celsius_per_hour': round(slope, 4),
            'direction': 'rising' if slope > 0.01 else 'falling' if slope < -0.01 else 'stable'
        }
    
    return stats


def generate_histogram(df: pd.DataFrame, output_file: str, hours: int = 24):
    """Generate temperature distribution histogram"""
    logger = logging.getLogger(__name__)
    
    # Filter data for specified time period
    if hours > 0:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        df_filtered = df[df.index >= cutoff_time]
    else:
        df_filtered = df
    
    if df_filtered.empty:
        logger.warning("No data available for histogram")
        return
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Plot histogram
    plt.hist(df_filtered['temperature_celsius'], bins=30, alpha=0.7, 
             color='blue', edgecolor='black')
    
    plt.title(f'Temperature Distribution - Last {hours} Hours' if hours > 0 else 'Temperature Distribution - All Data')
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # Add statistics lines
    mean_temp = df_filtered['temperature_celsius'].mean()
    median_temp = df_filtered['temperature_celsius'].median()
    
    plt.axvline(mean_temp, color='red', linestyle='--', label=f'Mean: {mean_temp:.2f}°C')
    plt.axvline(median_temp, color='green', linestyle='--', label=f'Median: {median_temp:.2f}°C')
    
    plt.legend()
    plt.tight_layout()
    
    # Save histogram
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Temperature histogram saved: {output_file}")


def print_statistics_report(stats: dict):
    """Print formatted statistics report"""
    if not stats:
        print("No statistics available")
        return
    
    print("\n" + "="*50)
    print("TEMPERATURE MONITORING STATISTICS")
    print("="*50)
    
    print(f"\nPeriod: {stats['period']}")
    print(f"Records: {stats['record_count']}")
    
    if 'time_range' in stats:
        print(f"Start: {stats['time_range']['start']}")
        print(f"End: {stats['time_range']['end']}")
        print(f"Duration: {stats['time_range']['duration_hours']:.2f} hours")
    
    print(f"\nTemperature (Celsius):")
    print(f"  Min:    {stats['celsius']['min']}°C")
    print(f"  Max:    {stats['celsius']['max']}°C")
    print(f"  Mean:   {stats['celsius']['mean']}°C")
    print(f"  Median: {stats['celsius']['median']}°C")
    print(f"  Std:    {stats['celsius']['std']}°C")
    
    print(f"\nTemperature (Fahrenheit):")
    print(f"  Min:    {stats['fahrenheit']['min']}°F")
    print(f"  Max:    {stats['fahrenheit']['max']}°F")
    print(f"  Mean:   {stats['fahrenheit']['mean']}°F")
    print(f"  Median: {stats['fahrenheit']['median']}°F")
    print(f"  Std:    {stats['fahrenheit']['std']}°F")
    
    if 'trend' in stats:
        print(f"\nTrend Analysis:")
        print(f"  Slope: {stats['trend']['slope_celsius_per_hour']:.4f}°C/hour")
        print(f"  Direction: {stats['trend']['direction']}")
    
    print("\n" + "="*50)


def main():
    """Main analysis function"""
    parser = argparse.ArgumentParser(description='Analyze temperature monitoring data')
    parser.add_argument('--data-file', '-d', default='data/temperature_data.json',
                        help='Path to temperature data file')
    parser.add_argument('--hours', '-t', type=int, default=24,
                        help='Number of recent hours to analyze (0 for all data)')
    parser.add_argument('--output-dir', '-o', default='analysis',
                        help='Output directory for charts and reports')
    parser.add_argument('--no-charts', action='store_true',
                        help='Skip chart generation')
    parser.add_argument('--stats-only', action='store_true',
                        help='Only show statistics, no file output')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load data
        logger.info(f"Loading temperature data from {args.data_file}")
        df = load_temperature_data(args.data_file)
        
        # Generate statistics
        logger.info("Generating statistics...")
        stats = generate_statistics_report(df, args.hours)
        
        # Print statistics
        print_statistics_report(stats)
        
        if not args.stats_only:
            # Create output directory
            output_dir = Path(args.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Generate charts
            if not args.no_charts:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Temperature chart
                chart_file = output_dir / f"temperature_chart_{timestamp}.png"
                generate_temperature_chart(df, str(chart_file), args.hours)
                
                # Histogram
                hist_file = output_dir / f"temperature_histogram_{timestamp}.png"
                generate_histogram(df, str(hist_file), args.hours)
            
            # Save statistics to JSON
            stats_file = output_dir / f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Statistics saved: {stats_file}")
        
        logger.info("Analysis complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
