from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
import logging
import time
from .serial_connection import SerialConnection
from .wifi_connection import WiFiConnection
from .bluetooth_connection import BluetoothConnection
from src.utils.config_manager import ConfigManager
from src.utils.connection_monitor import ConnectionMonitor

class ConnectionManager:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.connections = {
            'serial': SerialConnection(),
            'wifi': WiFiConnection(),
            'bluetooth': BluetoothConnection()
        }
        self.active_connection = None
        self.last_data = None
        self.last_read_time = 0
        self.retry_count = 0
        self.max_retries = 3
        self.cache_timeout = float(os.getenv('UPDATE_INTERVAL', 5000)) / 1000
        self.connection_priority = os.getenv('CONNECTION_PRIORITY', 'wifi,bluetooth,serial').split(',')
        config = ConfigManager()
        monitor = ConnectionMonitor(self)
        monitor.start()

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

    def connect(self, connection_type: str) -> bool:
        try:
            connection = self.connections.get(connection_type)
            if not connection:
                self.logger.error(f"Unknown connection type: {connection_type}")
                return False

            self.logger.info(f"Attempting to connect via {connection_type}")
            success = connection.connect()
            
            if success:
                self.active_connection = connection
                self.retry_count = 0
                self.logger.info(f"Successfully connected via {connection_type}")
            else:
                self.logger.warning(f"Failed to connect via {connection_type}")
                
            return success
        except Exception as e:
            self.logger.error(f"Error connecting via {connection_type}: {str(e)}")
            return False

    def try_reconnect(self) -> bool:
        if self.retry_count >= self.max_retries:
            self.logger.error("Max reconnection attempts reached")
            return False

        self.retry_count += 1
        for conn_type in self.connection_priority:
            if self.connect(conn_type):
                return True
        return False

    def read_data(self) -> Optional[Dict]:
        current_time = time.time()
        
        # Return cached data if within timeout
        if (current_time - self.last_read_time) < self.cache_timeout:
            return self.last_data

        if not self.active_connection:
            if not self.try_reconnect():
                return None

        try:
            data = self.active_connection.read_data()
            if data:
                self.last_data = data
                self.last_read_time = current_time
                self.retry_count = 0
                return data
            else:
                self.logger.warning("No data received")
                if self.try_reconnect():
                    return self.read_data()
                return None
        except Exception as e:
            self.logger.error(f"Error reading data: {str(e)}")
            if self.try_reconnect():
                return self.read_data()
            return None

    def disconnect(self) -> bool:
        try:
            if self.active_connection:
                success = self.active_connection.disconnect()
                if success:
                    self.active_connection = None
                    self.last_data = None
                    self.retry_count = 0
                return success
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting: {str(e)}")
            return False

    def get_connection_status(self) -> Dict:
        return {
            'active_connection': self.active_connection.__class__.__name__ if self.active_connection else None,
            'retry_count': self.retry_count,
            'last_read_time': self.last_read_time,
            'has_cached_data': self.last_data is not None
        }
