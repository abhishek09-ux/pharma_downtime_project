import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Step 1: Generate synthetic dataset
np.random.seed(42)
data = {
    "machine_id": np.random.randint(1, 50, 200),        # 50 machines
    "avg_temp": np.random.uniform(40, 120, 200),         # Avg temperature
    "avg_vibration": np.random.uniform(0.1, 5.0, 200),   # Avg vibration level
    "past_failures": np.random.randint(0, 10, 200),      # Past failures
    "downtime_next_week": np.random.randint(0, 2, 200)   # Target (0 = No, 1 = Yes)
}

df = pd.DataFrame(data)

# Step 2: Split data
X = df.drop(columns=["downtime_next_week"])
y = df["downtime_next_week"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 3: Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Step 4: Save model
joblib.dump(model, "app/utils/downtime_model.pkl")
print("✅ Model trained and saved as downtime_model.pkl")
