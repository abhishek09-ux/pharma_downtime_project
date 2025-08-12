# app/ml/model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

MODEL_PATH = "app/ml/downtime_model.pkl"

def train_model():
    # Example dataset (later replaced with real production line data)
    data = pd.DataFrame({
        "temperature": [45, 50, 55, 70, 65, 40],
        "vibration": [0.3, 0.4, 0.5, 0.9, 0.85, 0.2],
        "load": [75, 80, 85, 95, 90, 70],
        "downtime": [0, 0, 1, 1, 1, 0]  # 1 = downtime happened, 0 = no downtime
    })

    X = data[["temperature", "vibration", "load"]]
    y = data["downtime"]

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    print("Model trained and saved.")

def predict_downtime(temperature, vibration, load):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not found! Train it first.")

    model = joblib.load(MODEL_PATH)
    prediction = model.predict([[temperature, vibration, load]])
    return int(prediction[0])

## Removed invalid standalone Column definition. If needed, add as a field in your ORM model class in app/models/downtime.py.
## Removed invalid standalone Column definition. If needed, add as a field in your ORM model class.
