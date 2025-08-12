# train_downtime_model.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# -----------------------------
# 1. Generate Synthetic Downtime Dataset
# -----------------------------
np.random.seed(42)

# Number of synthetic samples
n_samples = 1000

# Example features (replace with real sensor data features later)
temperature = np.random.normal(loc=75, scale=5, size=n_samples)  # Avg temp ~75°C
vibration = np.random.normal(loc=0.5, scale=0.1, size=n_samples)  # Vibration intensity
load = np.random.normal(loc=70, scale=10, size=n_samples)         # Machine load (%)
pressure = np.random.normal(loc=30, scale=5, size=n_samples)      # Pressure (psi)

# Target variable: downtime event (1 = downtime, 0 = normal)
# Higher temperature, vibration, or load increases chance of downtime
downtime_prob = (
    0.3 * ((temperature - 70) / 10) +
    0.4 * ((vibration - 0.4) / 0.2) +
    0.3 * ((load - 65) / 15)
)
downtime = (np.random.rand(n_samples) < downtime_prob).astype(int)

# Create DataFrame
df = pd.DataFrame({
    'temperature': temperature,
    'vibration': vibration,
    'load': load,
    'pressure': pressure,
    'downtime': downtime
})

print("Sample Data:")
print(df.head())

# -----------------------------
# 2. Train Random Forest Model
# -----------------------------
X = df.drop(columns=['downtime'])
y = df['downtime']

# Split into train & test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluation
print("\nModel Performance:")
print(classification_report(y_test, y_pred))

# -----------------------------
# 3. Save Model as downtime_model.pkl
# -----------------------------
joblib.dump(model, "downtime_model.pkl")
print("\n✅ Model saved as downtime_model.pkl")
