import serial
import json
import logging
from typing import Optional, Dict
from dotenv import load_dotenv
import os

class SensorHandler:
    def __init__(self):
        load_dotenv()
        self.port = os.getenv('ARDUINO_PORT', 'COM3')
        self.baudrate = int(os.getenv('BAUDRATE', '115200'))
        self.serial = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='sensor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.logger.info(f"Connected to sensor on {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to sensor: {e}")
            return False

    def read_data(self) -> Optional[Dict]:
        if not self.serial or not self.serial.is_open:
            return None

        try:
            if self.serial.in_waiting:
                data = self.serial.readline().decode('utf-8').strip()
                return json.loads(data)
        except Exception as e:
            self.logger.error(f"Error reading sensor data: {e}")
            return None