import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv

class WeatherCore:
    def __init__(self):
        self.setup_config()
        self.setup_logging()
        self.setup_processor()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def setup_config(self):
        load_dotenv()
        self.config = {
            'hardware': {
                'arduino_port': os.getenv('ARDUINO_PORT', 'COM3'),
                'baudrate': int(os.getenv('BAUDRATE', '115200')),
                'device_name': os.getenv('DEVICE_NAME', 'WeatherStation'),
                'sensor_update_interval': int(os.getenv('SENSOR_UPDATE_INTERVAL', '5'))
            },
            'model': {
                'path': os.getenv('MODEL_PATH', 'models/weather_model.joblib'),
                'buffer_size': int(os.getenv('BUFFER_SIZE', '1000')),
                'min_data_points': int(os.getenv('MIN_DATA_POINTS', '24')),
                'training_interval': int(os.getenv('TRAINING_INTERVAL', '100'))
            },
            'connections': {
                'wifi_host': os.getenv('WIFI_HOST', '192.168.4.1'),
                'websocket_port': int(os.getenv('WEBSOCKET_PORT', '8765')),
                'bt_device_name': os.getenv('BT_DEVICE_NAME', 'ESP32-Weather')
            }
        }

    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename='logs/weather_system.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_processor(self):
        self.scaler = StandardScaler()
        self.data_cache = []
        self.cache_size = self.config['model']['buffer_size']

    def process_data(self, data: Dict) -> Optional[Dict]:
        try:
            if self.validate_data(data):
                self.data_cache.append(data)
                if len(self.data_cache) > self.cache_size:
                    self.data_cache.pop(0)
                return data
            return None
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return None

    def validate_data(self, data: Dict) -> bool:
        try:
            required_fields = {'temperature', 'humidity', 'pressure'}
            if not all(field in data for field in required_fields):
                return False
                
            valid_ranges = {
                'temperature': (-40, 80),
                'humidity': (0, 100),
                'pressure': (900, 1100)
            }
            
            return all(
                valid_ranges[field][0] <= data[field] <= valid_ranges[field][1]
                for field in required_fields
            )
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False