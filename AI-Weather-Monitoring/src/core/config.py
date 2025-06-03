from typing import Dict
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self._config = {
            'hardware': {
                'arduino_port': os.getenv('ARDUINO_PORT', 'COM3'),
                'baudrate': int(os.getenv('BAUDRATE', '115200')),
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

    def get(self, *keys) -> any:
        value = self._config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value

config = Config()