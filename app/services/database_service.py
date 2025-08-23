# app/services/database_service.py
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.downtime import Base, SensorReading, Downtime
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

class DatabaseService:
    def __init__(self):
        self.db: Session = None
    
    def get_db_session(self):
        """Get database session"""
        if not self.db:
            self.db = SessionLocal()
        return self.db
    
    def close_db_session(self):
        """Close database session"""
        if self.db:
            self.db.close()
            self.db = None
    
    def save_sensor_reading(self, sensor_data, machine_id="Machine1"):
        """Save sensor reading to database"""
        try:
            db = self.get_db_session()
            
            # Calculate shift
            current_hour = datetime.now().hour
            if 6 <= current_hour < 14:
                shift = 1  # Day
            elif 14 <= current_hour < 22:
                shift = 2  # Evening
            else:
                shift = 3  # Night
            
            # Get risk assessment
            from main import sensor_manager
            risk_score = sensor_manager.calculate_downtime_risk()
            status = sensor_manager.get_status_from_risk(risk_score)
            
            # Create sensor reading record
            reading = SensorReading(
                machine_id=machine_id,
                timestamp=datetime.utcnow(),
                ambient_temperature=sensor_data["temperature"]["value"],
                machine_temperature=sensor_data["machine_temperature"]["value"],
                humidity=sensor_data["humidity"]["value"],
                vibration=sensor_data["vibration"]["value"],
                current=sensor_data["current"]["value"],
                load=sensor_data["load"]["value"],
                shift=shift,
                risk_score=risk_score,
                status=status,
                raspberry_pi_mode=sensor_data.get("raspberry_pi", False),
                sensor_mode=sensor_data["temperature"]["status"]
            )
            
            # Add ML predictions if available
            try:
                from app.ml.model import predict_downtime
                ml_result = predict_downtime(
                    reading.ambient_temperature,
                    reading.machine_temperature, 
                    reading.humidity,
                    reading.vibration,
                    reading.current,
                    reading.shift
                )
                reading.ml_downtime_probability = ml_result['downtime_probability']
                reading.ml_predicted_downtime = ml_result['downtime_predicted']
            except Exception as e:
                logger.warning(f"ML prediction for DB failed: {e}")
                reading.ml_downtime_probability = 0.0
                reading.ml_predicted_downtime = False
            
            db.add(reading)
            db.commit()
            
            logger.debug(f"💾 Saved sensor reading: {status} risk={risk_score:.3f}")
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            if self.db:
                self.db.rollback()
    
    def save_downtime_event(self, machine_id, reason, duration_minutes=0.0):
        """Save downtime event to database"""
        try:
            db = self.get_db_session()
            
            downtime = Downtime(
                machine_id=machine_id,
                reason=reason,
                duration_minutes=duration_minutes,
                timestamp=datetime.utcnow()
            )
            
            db.add(downtime)
            db.commit()
            
            logger.info(f"⚠️ Downtime event saved: {machine_id} - {reason}")
            
        except Exception as e:
            logger.error(f"Downtime save error: {e}")
            if self.db:
                self.db.rollback()
    
    def get_recent_readings(self, machine_id=None, limit=100):
        """Get recent sensor readings"""
        try:
            db = self.get_db_session()
            
            query = db.query(SensorReading)
            if machine_id:
                query = query.filter(SensorReading.machine_id == machine_id)
            
            readings = query.order_by(SensorReading.timestamp.desc()).limit(limit).all()
            return readings
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_downtime_events(self, machine_id=None, limit=50):
        """Get recent downtime events"""
        try:
            db = self.get_db_session()
            
            query = db.query(Downtime)
            if machine_id:
                query = query.filter(Downtime.machine_id == machine_id)
            
            events = query.order_by(Downtime.timestamp.desc()).limit(limit).all()
            return events
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            db = self.get_db_session()
            
            # Recent readings count
            total_readings = db.query(SensorReading).count()
            
            # Recent downtime events
            total_downtime = db.query(Downtime).count()
            
            # Risk distribution
            critical_count = db.query(SensorReading).filter(SensorReading.status == 'CRITICAL').count()
            warning_count = db.query(SensorReading).filter(SensorReading.status == 'WARNING').count()
            ok_count = db.query(SensorReading).filter(SensorReading.status == 'OK').count()
            
            return {
                'total_readings': total_readings,
                'total_downtime_events': total_downtime,
                'risk_distribution': {
                    'critical': critical_count,
                    'warning': warning_count,
                    'ok': ok_count
                }
            }
            
        except Exception as e:
            logger.error(f"Dashboard stats error: {e}")
            return {
                'total_readings': 0,
                'total_downtime_events': 0,
                'risk_distribution': {'critical': 0, 'warning': 0, 'ok': 0}
            }

# Global database service instance
db_service = DatabaseService()
