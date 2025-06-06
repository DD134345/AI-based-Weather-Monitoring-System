import os
import numpy as np
import pandas as pd
from sklearn.ensemble import StackingRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import xgboost as xgb
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import joblib
from dotenv import load_dotenv
from src.utils.logger import LoggerMixin

class EnhancedWeatherPredictor(LoggerMixin):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.model_path = os.getenv('MODEL_PATH', 'models/weather_model.joblib')
        self.model = self._load_model() or RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.data_buffer = []
        self.min_samples = 24 * 7  # 7 days minimum
        self.setup_logging()
        self.setup_models()
        self.setup_scalers()

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

    def setup_models(self):
        # Create specialized models for each weather parameter
        estimators = [
            ('rf', RandomForestRegressor(
                n_estimators=500,
                max_depth=15,
                min_samples_split=5,
                n_jobs=-1,
                random_state=42
            )),
            ('xgb', xgb.XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=8,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )),
            ('gbm', GradientBoostingRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=8,
                subsample=0.8,
                random_state=42
            ))
        ]

        self.models = {
            'temperature': StackingRegressor(
                estimators=estimators,
                final_estimator=SVR(kernel='rbf')
            ),
            'humidity': StackingRegressor(
                estimators=estimators,
                final_estimator=SVR(kernel='rbf')
            ),
            'pressure': StackingRegressor(
                estimators=estimators,
                final_estimator=SVR(kernel='rbf')
            )
        }

    def setup_scalers(self):
        self.scalers = {
            'temperature': RobustScaler(),
            'humidity': RobustScaler(),
            'pressure': RobustScaler()
        }

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
            
            self.data_buffer.append(processed_data)
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

    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'])
        
        # Advanced feature engineering
        for param in ['temperature', 'humidity', 'pressure']:
            # Time-based features
            df[f'{param}_hour_avg'] = df.groupby(df['datetime'].dt.hour)[param].transform('mean')
            df[f'{param}_day_avg'] = df.groupby(df['datetime'].dt.day)[param].transform('mean')
            
            # Rolling statistics
            df[f'{param}_rolling_mean_6h'] = df[param].rolling(6).mean()
            df[f'{param}_rolling_mean_24h'] = df[param].rolling(24).mean()
            df[f'{param}_rolling_std_24h'] = df[param].rolling(24).std()
            
            # Rate of change
            df[f'{param}_rate_1h'] = df[param].diff(1)
            df[f'{param}_rate_6h'] = df[param].diff(6)
            
            # Scale features
            df[param] = self.scalers[param].fit_transform(df[[param]])

        # Weather pattern features
        df['temp_humidity_ratio'] = df['temperature'] / df['humidity']
        df['pressure_change_rate'] = df['pressure'].diff().rolling(6).mean()
        
        return df.dropna()

    async def train_model(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Train models with advanced validation"""
        try:
            df = self.prepare_features(historical_data)
            metrics = {}
            
            # Use time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            
            for param in ['temperature', 'humidity', 'pressure']:
                feature_cols = [col for col in df.columns if col.startswith(param) or 
                              col in ['hour', 'day', 'temp_humidity_ratio', 'pressure_change_rate']]
                
                X = df[feature_cols].values
                y = df[param].values
                
                # Cross validation with time series split
                scores = cross_val_score(
                    self.models[param],
                    X, y,
                    cv=tscv,
                    scoring='neg_root_mean_squared_error'
                )
                
                # Train final model
                self.models[param].fit(X, y)
                
                # Store metrics
                metrics[param] = {
                    'rmse': float(-scores.mean()),
                    'std': float(scores.std())
                }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Training error: {e}")
            return {}

    async def predict_weather(self, recent_data: List[Dict], days_ahead: int = 7) -> List[Dict]:
        """Generate detailed weather predictions"""
        try:
            df = self.prepare_features(recent_data)
            predictions = []
            
            current_features = df.iloc[-1:]
            current_date = pd.to_datetime(df.iloc[-1]['timestamp'])
            
            for day in range(days_ahead * 24):  # Predict every hour
                next_date = current_date + timedelta(hours=day+1)
                
                prediction = {
                    'timestamp': next_date.isoformat(),
                    'temperature': self._predict_parameter('temperature', current_features),
                    'humidity': self._predict_parameter('humidity', current_features),
                    'pressure': self._predict_parameter('pressure', current_features),
                }
                
                prediction['weather_type'] = self._determine_weather_type(prediction)
                prediction['confidence'] = self._calculate_confidence(prediction)
                
                predictions.append(prediction)
                current_features = self._update_features(current_features, prediction)
            
            return predictions
            
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return []