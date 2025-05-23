import pandas as pd
from typing import Dict, Optional, List
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import numpy as np
from sklearn.preprocessing import StandardScaler

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
                'timestamp': datetime.now().isoformat()
            }
            
            if not self._validate_data(processed_data):
                return None
                
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
            
    def prepare_for_prediction(self, window_size=24) -> Optional[np.ndarray]:
        """Prepare recent data for weather prediction"""
        try:
            if len(self.data_cache) < window_size:
                return None

            recent_data = self.data_cache[-window_size:]
            features = np.array([[d['temperature'], d['humidity'], d['pressure']] 
                               for d in recent_data])
            
            return self.scaler.fit_transform(features)
            
        except Exception as e:
            self.logger.error(f"Error preparing prediction data: {e}")
            return None