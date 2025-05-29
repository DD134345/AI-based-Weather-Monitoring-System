import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import os
from dotenv import load_dotenv
import joblib
from typing import Dict, Optional, List
from src.utils.logger import LoggerMixin

class WeatherPredictor(LoggerMixin):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.model_path = os.getenv('MODEL_PATH', 'models/weather_model.joblib')
        self.model = self._load_model() or RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.data = []

    def _load_model(self) -> Optional[RandomForestRegressor]:
        try:
            if os.path.exists(self.model_path):
                return joblib.load(self.model_path)
        except Exception as e:
            self.log_error(f"Error loading model: {e}")
        return None

    def save_model(self):
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            self.log_info("Model saved successfully")
        except Exception as e:
            self.log_error(f"Error saving model: {e}")

    def process_sensor_data(self, data: Dict) -> Optional[Dict]:
        """Process incoming sensor data and make prediction"""
        try:
            if not self.validate_weather_data(data):
                return None

            processed_data = {
                'temperature': float(data.get('temperature')),
                'humidity': float(data.get('humidity')),
                'pressure': float(data.get('pressure')),
                'timestamp': datetime.now().isoformat()
            }
            
            self.data.append(processed_data)
            prediction = self.predict([
                processed_data['temperature'],
                processed_data['humidity'],
                processed_data['pressure']
            ])
            
            return {
                'current': processed_data,
                'prediction': self.decode_prediction(prediction)
            }
            
        except Exception as e:
            self.log_error(f"Error processing sensor data: {e}")
            return None

    def predict(self, features: List[float]) -> int:
        """Make weather prediction from sensor data"""
        try:
            if not self.model:
                self.log_error("No model available for prediction")
                return 0

            prediction = self.model.predict(np.array(features).reshape(1, -1))
            return int(prediction[0])
        except Exception as e:
            self.log_error(f"Prediction error: {e}")
            return 0

    def validate_weather_data(self, data: Dict) -> bool:
        """Validate weather sensor readings"""
        try:
            required = ['temperature', 'humidity', 'pressure']
            if not all(k in data for k in required):
                self.log_error("Missing required weather parameters")
                return False
                
            valid_ranges = {
                'temperature': (-50, 60),
                'humidity': (0, 100),
                'pressure': (900, 1100)
            }
            
            for param, (min_val, max_val) in valid_ranges.items():
                value = float(data[param])
                if not min_val <= value <= max_val:
                    self.log_error(f"Invalid {param} value: {value}")
                    return False
                    
            return True
            
        except Exception as e:
            self.log_error(f"Validation error: {e}")
            return False

    def decode_prediction(self, code: int) -> str:
        """Convert prediction code to weather description"""
        weather_codes = {
            0: "Clear",
            1: "Partly Cloudy",
            2: "Rain Likely",
            3: "Heavy Rain"
        }
        return weather_codes.get(code, "Unknown")