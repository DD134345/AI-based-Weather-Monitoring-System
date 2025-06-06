from dotenv import load_dotenv
import os
from typing import Dict, Any

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'config'):
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
                'wifi': {
                    'host': os.getenv('WIFI_HOST', '192.168.4.1'),
                    'port': int(os.getenv('WIFI_PORT', '80')),
                    'ssid': os.getenv('WIFI_SSID', 'WeatherStation'),
                    'password': os.getenv('WIFI_PASSWORD', 'weather123')
                },
                'bluetooth': {
                    'device_name': os.getenv('BT_DEVICE_NAME', 'WeatherStation'),
                    'service_uuid': os.getenv('BT_SERVICE_UUID', '181A')
                },
                'system': {
                    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                    'cache_size': int(os.getenv('CACHE_SIZE', '1000'))
                }
            }
    
    def get(self, section: str, key: str) -> Any:
        """Get a configuration value"""
        return self.config.get(section, {}).get(key)
    
    def get_section(self, section: str) -> Dict:
        """Get an entire configuration section"""
        return self.config.get(section, {})
