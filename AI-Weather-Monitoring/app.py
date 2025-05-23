from src.controller import WeatherController
import logging
import asyncio
from bleak import BleakScanner, BleakClient
import json
from datetime import datetime

class BluetoothService:
    def __init__(self):
        self.WEATHER_SERVICE_UUID = "181A"  # Environmental Sensing service
        self.CHARACTERISTIC_UUID = "2A6E"   # Temperature characteristic
        self.DEVICE_NAME = "WeatherStation"
        self.client = None
        self.logger = logging.getLogger(__name__)

    async def scan_for_device(self):
        """Scan for the weather station device"""
        try:
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name == self.DEVICE_NAME:
                    return device
            return None
        except Exception as e:
            self.logger.error(f"Scan error: {e}")
            return None

    async def connect(self):
        """Connect to the weather station"""
        try:
            device = await self.scan_for_device()
            if device:
                self.client = BleakClient(device.address)
                await self.client.connect()
                self.logger.info(f"Connected to {device.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def read_sensor_data(self):
        """Read sensor data from the device"""
        try:
            if not self.client or not self.client.is_connected:
                await self.connect()
            
            data = await self.client.read_gatt_char(self.CHARACTERISTIC_UUID)
            return self.parse_sensor_data(data)
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            return None

    def parse_sensor_data(self, data):
        """Parse the raw sensor data"""
        try:
            decoded_data = data.decode('utf-8')
            sensor_data = json.loads(decoded_data)
            return {
                'temperature': sensor_data.get('temperature'),
                'humidity': sensor_data.get('humidity'),
                'pressure': sensor_data.get('pressure'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None

    async def disconnect(self):
        """Disconnect from the device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.logger.info("Disconnected from weather station")

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        bluetooth_service = BluetoothService()
        controller = WeatherController(bluetooth_service)
        logger.info("Starting Weather Monitoring System")
        await controller.start()
    except KeyboardInterrupt:
        logger.info("Shutting down Weather Monitoring System")
        await bluetooth_service.disconnect()
    except Exception as e:
        logger.error(f"System error: {e}")

if __name__ == '__main__':
    asyncio.run(main())