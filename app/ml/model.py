# app/ml/model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import logging
import warnings

# Suppress sklearn warnings for production
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

logger = logging.getLogger(__name__)

MODEL_PATH = "app/ml/downtime_model.pkl"

def create_pharmaceutical_training_data():
    """Create realistic pharmaceutical industry training data"""
    np.random.seed(42)  # For reproducible results
    
    # Generate 1000 samples of realistic pharmaceutical equipment data
    n_samples = 1000
    
    # Realistic ranges for pharmaceutical equipment
    data = []
    
    for i in range(n_samples):
        # Ambient temperature (20-30°C normal, higher indicates issues)
        amb_temp = np.random.normal(23, 2)
        
        # Machine temperature (65-85°C normal operation)
        if np.random.random() < 0.7:  # 70% normal operation
            machine_temp = np.random.normal(75, 5)
        else:  # 30% potential issues
            machine_temp = np.random.normal(90, 8)  # Overheating
        
        # Humidity (45-65% optimal for pharma)
        humidity = np.random.normal(55, 8)
        
        # Vibration (0.5-2.5G normal, >4G problematic)
        if np.random.random() < 0.8:  # 80% normal vibration
            vibration = np.random.normal(1.5, 0.5)
        else:  # 20% high vibration
            vibration = np.random.normal(5.0, 1.5)
        
        # Current (2-6A normal for pharma equipment)
        if np.random.random() < 0.75:  # 75% normal current
            current = np.random.normal(3.5, 0.8)
        else:  # 25% high current
            current = np.random.normal(7.0, 1.0)
        
        # Shift (1=day, 2=evening, 3=night)
        shift = np.random.choice([1, 2, 3], p=[0.4, 0.35, 0.25])
        
        # Calculate downtime probability based on realistic factors
        downtime_risk = 0.0
        
        # Temperature factors
        if amb_temp > 28:
            downtime_risk += 0.2
        if machine_temp > 85:
            downtime_risk += 0.3
        if machine_temp > 95:
            downtime_risk += 0.4
        
        # Vibration factor (critical for pharma precision)
        if vibration > 3.0:
            downtime_risk += 0.3
        if vibration > 5.0:
            downtime_risk += 0.5
        
        # Current factor
        if current > 6.5:
            downtime_risk += 0.2
        
        # Humidity factor
        if humidity > 70 or humidity < 40:
            downtime_risk += 0.1
        
        # Shift factor (night shift has higher risk)
        if shift == 3:  # Night shift
            downtime_risk += 0.08
        elif shift == 2:  # Evening shift
            downtime_risk += 0.03
        
        # Random factor for real-world unpredictability
        downtime_risk += np.random.normal(0, 0.05)
        
        # Convert to binary classification (>0.4 = downtime likely)
        downtime = 1 if downtime_risk > 0.4 else 0
        
        data.append({
            'ambient_temp': round(amb_temp, 1),
            'machine_temp': round(machine_temp, 1),
            'humidity': round(max(0, min(100, humidity)), 1),
            'vibration': round(max(0, vibration), 2),
            'current': round(max(0, current), 2),
            'shift': shift,
            'downtime': downtime
        })
    
    return pd.DataFrame(data)

def train_model():
    """Train the downtime prediction model with realistic data"""
    logger.info("🔄 Creating pharmaceutical training dataset...")
    
    # Create realistic training data
    data = create_pharmaceutical_training_data()
    
    # Features and target
    features = ['ambient_temp', 'machine_temp', 'humidity', 'vibration', 'current', 'shift']
    X = data[features]
    y = data['downtime']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest model
    logger.info("🤖 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"✅ Model training completed!")
    logger.info(f"📊 Accuracy: {accuracy:.3f}")
    logger.info(f"📈 Training samples: {len(X_train)}")
    logger.info(f"🧪 Test samples: {len(X_test)}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("🔍 Feature Importance:")
    for _, row in feature_importance.iterrows():
        logger.info(f"   {row['feature']}: {row['importance']:.3f}")
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"💾 Model saved to: {MODEL_PATH}")
    
    return model, accuracy

def predict_downtime(ambient_temp, machine_temp, humidity, vibration, current, shift):
    """Predict downtime probability"""
    if not os.path.exists(MODEL_PATH):
        logger.warning("Model not found! Training new model...")
        train_model()

    try:
        model = joblib.load(MODEL_PATH)
        
        # Create DataFrame with proper feature names to avoid sklearn warnings
        feature_names = ['ambient_temp', 'machine_temp', 'humidity', 'vibration', 'current', 'shift']
        features_df = pd.DataFrame([[ambient_temp, machine_temp, humidity, vibration, current, shift]], 
                                 columns=feature_names)
        
        # Get prediction and probability
        prediction = model.predict(features_df)[0]
        
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(features_df)[0]
            downtime_prob = probability[1]  # Probability of downtime (class 1)
        else:
            downtime_prob = float(prediction)
        
        return {
            'downtime_predicted': bool(prediction),
            'downtime_probability': round(downtime_prob, 3),
            'risk_level': 'HIGH' if downtime_prob > 0.7 else 'MEDIUM' if downtime_prob > 0.4 else 'LOW'
        }
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {
            'downtime_predicted': False,
            'downtime_probability': 0.0,
            'risk_level': 'UNKNOWN'
        }

def retrain_model_with_new_data(new_data_file=None):
    """Retrain model with additional data"""
    logger.info("🔄 Retraining model with new data...")
    
    # Load existing model data
    base_data = create_pharmaceutical_training_data()
    
    # Add new data if provided
    if new_data_file and os.path.exists(new_data_file):
        logger.info(f"📁 Loading additional data from: {new_data_file}")
        new_data = pd.read_csv(new_data_file)
        base_data = pd.concat([base_data, new_data], ignore_index=True)
    
    # Retrain
    return train_model()

if __name__ == "__main__":
    # Train model when run directly
    logging.basicConfig(level=logging.INFO)
    train_model()
