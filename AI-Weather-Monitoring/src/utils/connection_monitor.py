from typing import Dict, Callable
import time
import threading

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