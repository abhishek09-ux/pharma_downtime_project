import pickle
import numpy as np

# Load pre-trained ML model
with open("ml_model.pkl", "rb") as file:
    model = pickle.load(file)

def predict_downtime(features: list):
    """Takes input features and returns downtime probability"""
    prediction = model.predict_proba(np.array(features))[0][1]
    return round(float(prediction), 4)  # Probability of downtime
