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
from functools import lru_cache
from abc import ABC, abstractmethod
from pathlib import Path


# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models' / 'saved_models'

# Model settings
WEATHER_PARAMS = ['temperature', 'humidity', 'pressure']
FEATURE_COLUMNS = ['hour', 'day', 'temp_humidity_ratio', 'pressure_change_rate']
VALID_RANGES = {
    'temperature': (-50, 60),
    'humidity': (0, 100),
    'pressure': (900, 1100)
}

class LoggerMixin:
    def log_error(self, message: str) -> None:
        logging.error(message)

    def log_info(self, message: str) -> None:
        logging.info(message)

    def log_warning(self, message: str) -> None:
        logging.warning(message)

    def log_critical(self, message: str) -> None:
        logging.critical(message)

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, context: str) -> None:
        error_msg = f"{context}: {str(error)}"
        if isinstance(error, (ValueError, KeyError)):
            self.logger.warning(f"Data validation failed: {error_msg}")
        elif isinstance(error, (pd.errors.EmptyDataError, pd.errors.OutOfBoundsDatetime)):
            self.logger.error(f"DataFrame operation failed: {error_msg}")
        else:
            self.logger.critical(f"Critical error occurred: {error_msg}")

class EnhancedWeatherPredictor(LoggerMixin):
    # Constants to reduce memory allocations
    WEATHER_PARAMS = ['temperature', 'humidity', 'pressure']
    FEATURE_COLUMNS = ['hour', 'day', 'temp_humidity_ratio', 'pressure_change_rate']
    VALID_RANGES = {
        'temperature': (-50, 60),
        'humidity': (0, 100),
        'pressure': (900, 1100)
    }

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
        self.setup_models()
        self.setup_scalers()
        self.feature_engineer = FeatureEngineer()
        self.error_handler = ErrorHandler()

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
                'temperature': float(data.get('temperature', 0.0)),
                'humidity': float(data.get('humidity', 0.0)),
                'pressure': float(data.get('pressure', 0.0)),
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
                
            for param, (min_val, max_val) in self.VALID_RANGES.items():
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

    def _prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Optimized feature engineering with vectorized operations"""
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'])
        
        # Vectorized operations for all parameters at once
        for param in self.WEATHER_PARAMS:
            # Group operations
            hour_groups = df.groupby(df['datetime'].dt.hour)[param]
            day_groups = df.groupby(df['datetime'].dt.day)[param]
            
            # Compute all features in parallel
            df[f'{param}_hour_avg'] = hour_groups.transform('mean')
            df[f'{param}_day_avg'] = day_groups.transform('mean')
            
            # Vectorized rolling operations
            rolling_data = df[param].rolling(window=24)
            df[f'{param}_rolling_mean_6h'] = df[param].rolling(window=6).mean()
            df[f'{param}_rolling_mean_24h'] = rolling_data.mean()
            df[f'{param}_rolling_std_24h'] = rolling_data.std()
            
            # Vectorized diff operations
            df[f'{param}_rate_1h'] = df[param].diff(1)
            df[f'{param}_rate_6h'] = df[param].diff(6)
            
            # Scale features using pre-initialized scalers
            df[param] = self.scalers[param].fit_transform(df[[param]])
        
        # Vectorized derived features
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
                    np.array(X), np.array(y),
                    cv=tscv,
                    scoring='neg_root_mean_squared_error'
                )
                
                # Train final model
                self.models[param].fit(X, np.asarray(y))
                
                # Store metrics
                metrics[param] = {
                    'rmse': float(-scores.mean()),
                    'std': float(scores.std())
                }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Training error: {e}")
            return {}

    def _predict_parameter(self, param: str, features) -> float:
        """Make prediction for a specific weather parameter"""
        try:
            feature_cols = [col for col in features.columns if col.startswith(param) or 
                          col in ['hour', 'day', 'temp_humidity_ratio', 'pressure_change_rate']]
            return float(self.models[param].predict(features[feature_cols]))
        except Exception as e:
            self.log_error(f"Error predicting {param}: {e}")
            return 0.0

    def _calculate_confidence(self, prediction: Dict) -> float:
        """Calculate confidence score for the prediction with enhanced metrics"""
        try:
            # Base confidence from parameter ranges
            temp_conf = min(1.0, max(0.0, 1 - abs(prediction['temperature']) / 50))
            humid_conf = min(1.0, max(0.0, 1 - abs(prediction['humidity'] - 50) / 50))
            press_conf = min(1.0, max(0.0, 1 - abs(prediction['pressure'] - 1013) / 100))
            
            # Add trend stability factor
            trend_stability = 1.0
            if len(self.data_buffer) > 24:
                recent_data = pd.DataFrame(self.data_buffer[-24:])
                for param in ['temperature', 'humidity', 'pressure']:
                    std = recent_data[param].std()
                    # Higher stability (lower std) increases confidence
                    trend_stability *= max(0.0, 1.0 - (std / 10))
            
            # Combine all factors
            base_confidence = (temp_conf + humid_conf + press_conf) / 3
            final_confidence = (base_confidence + trend_stability) / 2
            
            return round(final_confidence, 2)
            
        except Exception as e:
            self.log_error(f"Error calculating confidence: {e}")
            return 0.5

    @lru_cache(maxsize=128)
    def _get_weather_type(self, temp: float, humidity: float, pressure: float) -> str:
        """Cached weather type determination"""
        try:
            if pressure < 1000:
                if humidity > 80:
                    return "Heavy Rain"
                return "Rain Likely"
            elif humidity > 70:
                return "Partly Cloudy"
            return "Clear"
        except Exception as e:
            self.log_error(f"Error determining weather type: {e}")
            return "Unknown"

    def _determine_weather_type(self, prediction: Dict) -> str:
        return self._get_weather_type(
            prediction['temperature'],
            prediction['humidity'],
            prediction['pressure']
        )

    async def predict_weather(self, recent_data: List[Dict], days_ahead: int = 7) -> List[Dict]:
        """Optimized weather prediction with batched processing"""
        try:
            df = self.prepare_features(recent_data)
            predictions = []
            
            # Pre-allocate features matrix
            current_features = df.iloc[-1:].copy()
            current_date = pd.to_datetime(df.iloc[-1]['timestamp'])
            
            # Batch predictions for better performance
            BATCH_SIZE = 24  # Process one day at a time
            total_hours = days_ahead * 24
            
            for batch_start in range(0, total_hours, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_hours)
                batch_predictions = []
                
                for hour in range(batch_start, batch_end):
                    next_date = current_date + timedelta(hours=hour+1)
                    
                    # Parallel parameter prediction
                    pred_params = {
                        param: self._predict_parameter(param, current_features) 
                        for param in self.WEATHER_PARAMS
                    }
                    
                    prediction = {
                        'timestamp': next_date.isoformat(),
                        **pred_params
                    }
                    
                    # Add derived predictions
                    prediction['weather_type'] = self._determine_weather_type(prediction)
                    prediction['confidence'] = self._calculate_confidence(prediction)
                    
                    batch_predictions.append(prediction)
                    current_features = self._update_features(current_features, prediction)
                
                predictions.extend(batch_predictions)
            
            return predictions
                
        except Exception as e:
            self.log_error(f"Prediction error: {e}")
            return []
    
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """Optimized feature engineering with vectorized operations"""
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'])
        
        # Vectorized operations for all parameters at once
        for param in self.WEATHER_PARAMS:
            # Group operations
            hour_groups = df.groupby(df['datetime'].dt.hour)[param]
            day_groups = df.groupby(df['datetime'].dt.day)[param]
            
            # Compute all features in parallel
            df[f'{param}_hour_avg'] = hour_groups.transform('mean')
            df[f'{param}_day_avg'] = day_groups.transform('mean')
            
            # Vectorized rolling operations
            rolling_data = df[param].rolling(window=24)
            df[f'{param}_rolling_mean_6h'] = df[param].rolling(window=6).mean()
            df[f'{param}_rolling_mean_24h'] = rolling_data.mean()
            df[f'{param}_rolling_std_24h'] = rolling_data.std()
            
            # Vectorized diff operations
            df[f'{param}_rate_1h'] = df[param].diff(1)
            df[f'{param}_rate_6h'] = df[param].diff(6)
            
            # Scale features using pre-initialized scalers
            df[param] = self.scalers[param].fit_transform(df[[param]])
        
        # Vectorized derived features
        df['temp_humidity_ratio'] = df['temperature'] / df['humidity']
        df['pressure_change_rate'] = df['pressure'].diff().rolling(6).mean()
        
        return df.dropna()

    def _update_features(self, current_features: pd.DataFrame, prediction: Dict) -> pd.DataFrame:
        """Update features for the next prediction iteration"""
        try:
            new_features = current_features.copy()
            
            # Update base parameters
            for param in ['temperature', 'humidity', 'pressure']:
                new_features[param] = prediction[param]
                
                # Update time-based features
                new_features[f'{param}_hour_avg'] = new_features[param]  # Single point, use current
                new_features[f'{param}_day_avg'] = (
                    new_features[f'{param}_day_avg'] * 23 + new_features[param]
                ) / 24  # Rolling daily average
                
                # Update rolling statistics
                new_features[f'{param}_rolling_mean_6h'] = (
                    new_features[f'{param}_rolling_mean_6h'] * 5 + new_features[param]
                ) / 6
                new_features[f'{param}_rolling_mean_24h'] = (
                    new_features[f'{param}_rolling_mean_24h'] * 23 + new_features[param]
                ) / 24
                
                # Calculate rate of change
                new_features[f'{param}_rate_1h'] = (
                    new_features[param] - current_features[param].iloc[0]
                )
            
            # Update datetime and derived features
            new_features['datetime'] = pd.to_datetime(prediction['timestamp'])
            new_features['temp_humidity_ratio'] = new_features['temperature'] / new_features['humidity']
            new_features['pressure_change_rate'] = (
                new_features['pressure'] - current_features['pressure'].iloc[0]
            )
            
            return new_features
                
        except Exception as e:
            self.log_error(f"Error updating features: {e}")
            return current_features

    # Add this method for centralized error handling
    def _handle_error(self, error: Exception, context: str) -> None:
        """Centralized error handling with context"""
        error_msg = f"{context}: {str(error)}"
        self.log_error(error_msg)
        
        if isinstance(error, (ValueError, KeyError)):
            # Data validation errors
            self.log_warning(f"Data validation failed: {error_msg}")
        elif isinstance(error, (pd.errors.EmptyDataError, pd.errors.OutOfBoundsDatetime)):
            # DataFrame-related errors
            self.log_error(f"DataFrame operation failed: {error_msg}")
        else:
            # Unexpected errors
            self.log_critical(f"Critical error occurred: {error_msg}")
            # Could add error reporting to monitoring system here

DEFAULT_MODEL_CONFIGS = {
    'temperature': {
        'estimators': [
            ('rf', RandomForestRegressor(
                n_estimators=500,
                max_depth=15,
                min_samples_split=5,
                n_jobs=-1,
                random_state=42
            )),
            # ... other estimators
        ]
    }
    # ... configs for other parameters
}

class FeatureEngineer:
    """Handle all feature engineering operations"""
    
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        # Move feature engineering logic here
        return pd.DataFrame(data)
    
    def update_features(self, current_features: pd.DataFrame, 
                       prediction: Dict) -> pd.DataFrame:
        # Move feature update logic here
        return current_features.copy()

