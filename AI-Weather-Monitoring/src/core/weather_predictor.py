import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import logging
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class WeatherPredictor:
    def __init__(self):
        self.model_path = os.getenv('MODEL_PATH', 'models/weather_prediction_model.h5')
        self.model = self._load_model() or RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_model(self) -> Optional[RandomForestRegressor]:
        try:
            if os.path.exists(self.model_path):
                return joblib.load(self.model_path)
        except Exception as e:
            logging.error(f"Error loading model: {e}")
        return None

    def predict(self, features: List[float]) -> np.ndarray:
        try:
            return self.model.predict(np.array(features).reshape(1, -1))[0]
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return np.array([0, 0, 0])  # Default values for temp, humidity, pressure