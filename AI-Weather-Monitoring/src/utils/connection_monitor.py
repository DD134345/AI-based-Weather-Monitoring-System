from typing import Dict, Callable
import time
import threading
import logging

class ConnectionManager:
    def __init__(self):
        self.current_connection = None
        self.logger = logging.getLogger(__name__)

    async def _connect_bluetooth(self, device_name: str) -> bool:
        # Implement your Bluetooth connection logic here
        try:
            # Add your Bluetooth connection code
            return True
        except Exception as e:
            self.logger.error(f"Bluetooth connection error: {e}")
            return False

    async def _connect_wifi(self, host: str) -> bool:
        # Implement your WiFi connection logic here
        try:
            # Add your WiFi connection code
            return True
        except Exception as e:
            self.logger.error(f"WiFi connection error: {e}")
            return False

    async def _connect_serial(self, port: str, baudrate: int) -> bool:
        # Implement your Serial connection logic here
        try:
            # Add your Serial connection code
            return True
        except Exception as e:
            self.logger.error(f"Serial connection error: {e}")
            return False

    async def connect(self, connection_type: str, **params) -> bool:
        try:
            if connection_type == 'bluetooth':
                return await self._connect_bluetooth(params['device_name'])
            elif connection_type == 'wifi':
                return await self._connect_wifi(params['host'])
            elif connection_type == 'serial':
                return await self._connect_serial(params['port'], params['baudrate'])
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

class ConnectionMonitor:
    def __init__(self, connection_manager, check_interval: float = 5.0):
        self.connection_manager = connection_manager
        self.check_interval = check_interval
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self.monitor_thread = None

    def start(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        while self.running:
            status = self.connection_manager.get_connection_status()
            self._notify_callbacks(status)
            time.sleep(self.check_interval)

    def add_callback(self, name: str, callback: Callable):
        self.callbacks[name] = callback

    def remove_callback(self, name: str):
        self.callbacks.pop(name, None)

    def _notify_callbacks(self, status: Dict):
        for callback in self.callbacks.values():
            try:
                callback(status)
            except Exception:
                continue