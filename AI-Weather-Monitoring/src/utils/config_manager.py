from dotenv import load_dotenv
import os
from src.utils.connection_monitor import ConnectionMonitor
from src.utils.cache_manager import DataCache
from src.utils.connection_manager import ConnectionManager

class ConfigManager:
    def __init__(self):
        load_dotenv()
        self.config = {
            'hardware': {
                'arduino_port': os.getenv('ARDUINO_PORT', 'COM3'),
                'baudrate': int(os.getenv('BAUDRATE', '115200')),
                'device_name': os.getenv('DEVICE_NAME', 'WeatherStation')
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
                'cache_size': int(os.getenv('CACHE_SIZE', '1000')),
                'prediction_window': int(os.getenv('PREDICTION_WINDOW', '24')),
                'update_interval': int(os.getenv('UPDATE_INTERVAL', '5000')),
                'connection_priority': os.getenv('CONNECTION_PRIORITY', 'wifi,bluetooth,serial').split(',')
            }
        }

    def get(self, section: str, key: str):
        return self.config.get(section, {}).get(key)

    def get_section(self, section: str):
        return self.config.get(section, {})

config = ConfigManager()
connection_manager = ConnectionManager()
monitor = ConnectionMonitor(connection_manager)
monitor.start()

cache = DataCache()
data = connection_manager.read_data()
if data:
    cache.add_data(data)
