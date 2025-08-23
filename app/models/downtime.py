from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from app.core.database import Base
from datetime import datetime

class Downtime(Base):
    __tablename__ = "downtime_events"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)  # Machine identifier
    reason = Column(String)  # Reason for downtime
    duration_minutes = Column(Float)  # Duration in minutes
    timestamp = Column(DateTime, default=datetime.utcnow)  # Event time

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Sensor values
    ambient_temperature = Column(Float)
    machine_temperature = Column(Float)
    humidity = Column(Float)
    vibration = Column(Float)
    current = Column(Float)
    load = Column(Float)
    
    # Shift and status
    shift = Column(Integer)  # 1=day, 2=evening, 3=night
    
    # Risk assessment
    risk_score = Column(Float)
    status = Column(String)  # OK, WARNING, CRITICAL
    
    # ML predictions
    ml_downtime_probability = Column(Float)
    ml_predicted_downtime = Column(Boolean)
    
    # Sensor status
    raspberry_pi_mode = Column(Boolean, default=False)
    sensor_mode = Column(String)  # 'online', 'offline', 'simulated'
