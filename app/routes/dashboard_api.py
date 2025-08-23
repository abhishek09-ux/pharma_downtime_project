# app/routes/dashboard_api.py
from fastapi import APIRouter
from app.services.database_service import db_service
from typing import List, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/dashboard/stats")
def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics from database"""
    try:
        stats = db_service.get_dashboard_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Dashboard stats API error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": {
                'total_readings': 0,
                'total_downtime_events': 0,
                'risk_distribution': {'critical': 0, 'warning': 0, 'ok': 0}
            }
        }

@router.get("/api/sensor/history")
def get_sensor_history(machine_id: str = None, limit: int = 100) -> Dict[str, Any]:
    """Get historical sensor readings"""
    try:
        readings = db_service.get_recent_readings(machine_id, limit)
        
        # Convert to JSON-serializable format
        data = []
        for reading in readings:
            data.append({
                "id": reading.id,
                "machine_id": reading.machine_id,
                "timestamp": reading.timestamp.isoformat(),
                "ambient_temperature": reading.ambient_temperature,
                "machine_temperature": reading.machine_temperature,
                "humidity": reading.humidity,
                "vibration": reading.vibration,
                "current": reading.current,
                "load": reading.load,
                "shift": reading.shift,
                "risk_score": reading.risk_score,
                "status": reading.status,
                "ml_downtime_probability": reading.ml_downtime_probability,
                "ml_predicted_downtime": reading.ml_predicted_downtime,
                "raspberry_pi_mode": reading.raspberry_pi_mode,
                "sensor_mode": reading.sensor_mode
            })
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Sensor history API error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@router.get("/api/downtime/history")
def get_downtime_history(machine_id: str = None, limit: int = 50) -> Dict[str, Any]:
    """Get historical downtime events"""
    try:
        events = db_service.get_downtime_events(machine_id, limit)
        
        # Convert to JSON-serializable format
        data = []
        for event in events:
            data.append({
                "id": event.id,
                "machine_id": event.machine_id,
                "reason": event.reason,
                "duration_minutes": event.duration_minutes,
                "timestamp": event.timestamp.isoformat()
            })
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Downtime history API error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@router.get("/api/machines")
def get_machines() -> Dict[str, Any]:
    """Get list of all machines"""
    try:
        # Get unique machine IDs from sensor readings
        readings = db_service.get_recent_readings(limit=1000)
        machine_ids = list(set([r.machine_id for r in readings]))
        
        machines = []
        for machine_id in machine_ids:
            # Get latest reading for each machine
            latest_readings = db_service.get_recent_readings(machine_id, 1)
            if latest_readings:
                latest = latest_readings[0]
                machines.append({
                    "machine_id": machine_id,
                    "status": latest.status,
                    "risk_score": latest.risk_score,
                    "last_reading": latest.timestamp.isoformat(),
                    "raspberry_pi_mode": latest.raspberry_pi_mode,
                    "sensor_mode": latest.sensor_mode
                })
        
        return {
            "status": "success",
            "count": len(machines),
            "data": machines
        }
        
    except Exception as e:
        logger.error(f"Machines API error: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "data": []
        }
