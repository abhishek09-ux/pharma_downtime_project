import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# Load dataset
data = pd.read_csv("downtime_data.csv")

# Features and target
X = data[["temperature", "vibration", "machine_load", "shift"]]
y = data["downtime_occurred"]

# Split dataset into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train RandomForest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model
accuracy = model.score(X_test, y_test)
print(f"✅ Model Accuracy: {accuracy:.2f}")

# Save model
model_path = os.path.join("backend", "model", "downtime_predictor.pkl")
os.makedirs(os.path.dirname(model_path), exist_ok=True)
with open(model_path, "wb") as file:
    pickle.dump(model, file)

print(f"💾 Model saved to: {model_path}")

# ---- Test Prediction ----
# Example: Temperature=80, Vibration=0.4, Machine Load=0.85, Shift=3
test_input = [[80, 0.4, 0.85, 3]]
prediction = model.predict(test_input)[0]
print(f"🔮 Prediction for {test_input}: {'Downtime' if prediction == 1 else 'No Downtime'}")
