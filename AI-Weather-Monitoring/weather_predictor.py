from sklearn.ensemble import RandomForestRegressor
import joblib
import numpy as np
from typing import List, Dict

class WeatherPredictor:
    def __init__(self, model_path: str = 'models/weather_model.pkl'):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model_path = model_path
        
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the weather prediction model"""
        self.model.fit(X, y)
        joblib.dump(self.model, self.model_path)
        
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict weather conditions"""
        return self.model.predict(features)