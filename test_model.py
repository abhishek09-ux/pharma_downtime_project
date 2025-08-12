import pickle
import numpy as np

with open("backend/model/downtime_predictor.pkl", "rb") as f:
    model = pickle.load(f)

sample_features = [75.2, 0.32, 0.8, 1]  # Example: temp, vib, load, shift
prob = model.predict_proba(np.array(sample_features).reshape(1, -1))[0][1]
print(f"Predicted downtime probability: {prob:.2f}")

