import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, List, Optional

class WeatherDataProcessor:
    def __init__(self, cache_size: int = 1000):
        self.scaler = StandardScaler()
        self.setup_logging()
        self.data_cache = []
        self.cache_size = cache_size
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def setup_logging(self):
        logging.basicConfig(
            filename='data_processor.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def process_sensor_data(self, data: Dict) -> Optional[Dict]:
        """Process sensor data with validation and caching"""
        try:
            if not data:
                return None
                
            processed_data = {
                'temperature': float(data.get('temperature', 0)),
                'humidity': float(data.get('humidity', 0)),
                'pressure': float(data.get('pressure', 0)),
                'timestamp': data.get('timestamp')
            }
            
            # Async validation
            future = self.executor.submit(self._validate_data, processed_data)
            if not future.result():
                return None
                
            # Update cache
            self._update_cache(processed_data)
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            return None
            
    def _validate_data(self, data: Dict) -> bool:
        """Validate sensor readings"""
        try:
            return not any(
                value < -100 or value > 100 
                for key, value in data.items()
                if key not in ['pressure', 'timestamp']
            )
        except:
            return False
            
    def _update_cache(self, data: Dict) -> None:
        """Update data cache with size limit"""
        self.data_cache.append(data)
        if len(self.data_cache) > self.cache_size:
            self.data_cache.pop(0)
            
    def prepare_for_prediction(self, data_list, window_size=24):
        """Prepare data for weather prediction"""
        try:
            if not data_list:
                return None
                
            df = pd.DataFrame(data_list)
            
            # Calculate rolling averages
            df['temp_avg_24h'] = df['temperature'].rolling(window=window_size).mean()
            df['humidity_avg_24h'] = df['humidity'].rolling(window=window_size).mean()
            df['pressure_avg_24h'] = df['pressure'].rolling(window=window_size).mean()
            
            # Calculate rate of change
            df['temp_change'] = df['temperature'].diff()
            df['pressure_change'] = df['pressure'].diff()
            
            # Drop NaN values
            df = df.dropna()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error preparing data for prediction: {e}")
            return None