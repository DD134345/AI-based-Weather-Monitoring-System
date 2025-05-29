from typing import Dict, Optional
import time
import json
import os
from threading import Lock

class DataCache:
    def __init__(self, cache_size: int = 1000, cache_file: str = 'data/cache.json'):
        self.cache_size = cache_size
        self.cache_file = cache_file
        self.data_cache = []
        self.cache_lock = Lock()
        self.load_cache()

    def add_data(self, data: Dict) -> None:
        with self.cache_lock:
            self.data_cache.append({**data, 'timestamp': time.time()})
            if len(self.data_cache) > self.cache_size:
                self.data_cache.pop(0)
            self.save_cache()

    def get_recent_data(self, count: int) -> list:
        with self.cache_lock:
            return self.data_cache[-count:]

    def save_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.data_cache, f)

    def load_cache(self) -> None:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.data_cache = json.load(f)
        except Exception:
            self.data_cache = []