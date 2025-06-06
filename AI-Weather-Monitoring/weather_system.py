import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional, List, Callable, Any
import json
import click
from dotenv import load_dotenv
import serial
import aiohttp
from bleak import BleakClient, BleakScanner
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

# Configuration Management
class Config:
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
                    'sensor_update_interval': int(os.getenv('SENSOR_UPDATE_INTERVAL', '5'))
                },
                'connections': {
                    'wifi_host': os.getenv('WIFI_HOST', '192.168.4.1'),
                    'bt_device_name': os.getenv('BT_DEVICE_NAME', 'WeatherStation')
                },
                'model': {
                    'buffer_size': int(os.getenv('BUFFER_SIZE', '1000')),
                    'min_data_points': int(os.getenv('MIN_DATA_POINTS', '24'))
                }
            }

    def get(self, section: str, key: str) -> Any:
        return self.config.get(section, {}).get(key)

# Device Connection Manager
class DeviceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_type = None
        self.serial_conn = None
        self.ble_client = None
        self.wifi_url = None

    async def connect(self, connection_type: str, **kwargs) -> bool:
        self.connection_type = connection_type
        if connection_type == 'serial':
            return self._connect_serial(kwargs['port'], kwargs['baudrate'])
        elif connection_type == 'bluetooth':
            return await self._connect_bluetooth(kwargs['device_name'])
        elif connection_type == 'wifi':
            return await self._connect_wifi(kwargs['ip'])
        return False

    def _connect_serial(self, port: str, baudrate: int) -> bool:
        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            return True
        except Exception as e:
            self.logger.error(f"Serial connection failed: {e}")
            return False

    async def _connect_bluetooth(self, device_name: str) -> bool:
        try:
            device = await BleakScanner.find_device_by_name(device_name)
            if device:
                self.ble_client = BleakClient(device.address)
                await self.ble_client.connect()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Bluetooth connection failed: {e}")
            return False

    async def read_data(self) -> Optional[Dict]:
        try:
            if self.connection_type == 'serial':
                return await self._read_serial()
            elif self.connection_type == 'bluetooth':
                return await self._read_bluetooth()
            elif self.connection_type == 'wifi':
                return await self._read_wifi()
        except Exception as e:
            self.logger.error(f"Read error: {e}")
        return None

    async def disconnect(self):
        try:
            if self.serial_conn:
                self.serial_conn.close()
            elif self.ble_client:
                await self.ble_client.disconnect()
            self.connection_type = None
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")

# Weather System Manager
class WeatherSystem:
    def __init__(self):
        self.setup_logging()
        self.config = Config()
        self.device = DeviceManager()
        self.scaler = StandardScaler()
        self.data_buffer = []
        self.running = False

    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename=f'logs/system_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.running = True
        try:
            if not await self._establish_connection():
                self.logger.error("Failed to connect to weather station")
                return False

            while self.running:
                await self._process_cycle()
                await asyncio.sleep(self.config.get('hardware', 'sensor_update_interval'))
        except Exception as e:
            self.logger.error(f"System error: {e}")
            return False
        finally:
            await self.stop()

    async def _establish_connection(self) -> bool:
        connection_methods = [
            ('wifi', {'ip': self.config.get('connections', 'wifi_host')}),
            ('bluetooth', {'device_name': self.config.get('connections', 'bt_device_name')}),
            ('serial', {
                'port': self.config.get('hardware', 'arduino_port'),
                'baudrate': self.config.get('hardware', 'baudrate')
            })
        ]

        for method, params in connection_methods:
            if await self.device.connect(method, **params):
                self.logger.info(f"Connected via {method}")
                return True
        return False

    async def _process_cycle(self):
        try:
            data = await self.device.read_data()
            if data:
                self.data_buffer.append(data)
                if len(self.data_buffer) > self.config.get('model', 'buffer_size'):
                    self.data_buffer.pop(0)
                self.logger.info(f"Current conditions: {data}")
        except Exception as e:
            self.logger.error(f"Processing error: {e}")

    async def stop(self):
        self.running = False
        await self.device.disconnect()
        self.logger.info("System stopped")

# CLI Interface
@click.group()
def cli():
    """Weather Monitoring System CLI"""
    pass

@cli.command()
def start():
    """Start the weather monitoring system"""
    system = WeatherSystem()
    asyncio.run(system.start())

if __name__ == '__main__':
    cli()