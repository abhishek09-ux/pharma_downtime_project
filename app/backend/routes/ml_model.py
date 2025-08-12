import pickle
import numpy as np

MODEL_PATH = "ml_models/downtime_predictor.pkl"

# Load model at startup
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_downtime(features: list) -> float:
    """
    Predict downtime probability.
    :param features: list of numerical values [temp, vibration, load, shift, ...]
    :return: probability of downtime (0 to 1)
    """
    features_array = np.array(features).reshape(1, -1)
    probability = model.predict_proba(features_array)[0][1]  # Class 1 probability
    return round(probability, 4)
