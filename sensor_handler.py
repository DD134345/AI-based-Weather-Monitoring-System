import serial
import serial.tools.list_ports
import json
import time
from datetime import datetime
import logging

class ArduinoSensorHandler:
    def __init__(self, port='COM3', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            filename='sensor_handler.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def list_available_ports(self):
        """List all available COM ports"""
        ports = list(serial.tools.list_ports.comports())
        self.logger.info(f"Available ports: {[port.device for port in ports]}")
        return ports

    def connect(self):
        """Connect to Arduino"""
        try:
            # Check if port exists
            available_ports = self.list_available_ports()
            if not any(self.port in port.device for port in available_ports):
                self.logger.error(f"Port {self.port} not found. Available ports: {[port.device for port in available_ports]}")
                return False

            # Close if already open
            if self.serial and self.serial.is_open:
                self.serial.close()

            # Open new connection
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Flush input buffer
            self.serial.reset_input_buffer()
            
            self.logger.info(f"Successfully connected to {self.port}")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Serial connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while connecting: {e}")
            return False

    def read_sensor_data(self):
        """Read sensor data from Arduino"""
        try:
            if not self.serial or not self.serial.is_open:
                self.logger.warning("Serial connection not open, attempting to reconnect")
                if not self.connect():
                    return None

            # Wait for data to be available
            attempts = 0
            max_attempts = 5
            while attempts < max_attempts and not self.serial.in_waiting:
                time.sleep(0.2)
                attempts += 1

            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                self.logger.debug(f"Raw data received: {line}")
                
                if line:
                    try:
                        data = json.loads(line)
                        data['timestamp'] = datetime.now().timestamp()
                        self.logger.info(f"Parsed sensor data: {data}")
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON parsing error: {e}. Raw data: {line}")
                        return None
            else:
                self.logger.warning("No data received from Arduino")
                return None

        except serial.SerialException as e:
            self.logger.error(f"Serial communication error: {e}")
            self.serial = None
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading sensor data: {e}")
            return None

    def close(self):
        """Close serial connection"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                self.logger.info("Serial connection closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing serial connection: {e}")