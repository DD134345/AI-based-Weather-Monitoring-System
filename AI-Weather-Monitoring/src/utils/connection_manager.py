from typing import Optional, Dict
import logging
import time
from serial import Serial
import requests
from bleak import BleakClient
import asyncio
from dotenv import load_dotenv
import os
from src.utils.logger import LoggerMixin

class ConnectionManager(LoggerMixin):
    def __init__(self):
        super().__init__()  # Initialize logger
        load_dotenv()
        self.serial_port = os.getenv('ARDUINO_PORT', 'COM3')
        self.wifi_host = os.getenv('WIFI_HOST', '192.168.4.1')
        self.bt_device_name = os.getenv('BT_DEVICE_NAME', 'WeatherStation')
        self.active_connection = None
        self.serial = None
        self.ble_client = None

    async def connect(self, mode: str = 'auto') -> bool:
        self.log_info(f"Connecting using {mode} mode...")
        """Connect using specified mode or try all available modes"""
        if mode == 'serial':
            return self.connect_serial()
        elif mode == 'wifi':
            return self.connect_wifi()
        elif mode == 'bluetooth':
            return await self.connect_bluetooth()
        else:
            # Try all connection methods in order
            if self.connect_serial():
                return True
            if self.connect_wifi():
                return True
            if await self.connect_bluetooth():
                return True
        return False

    def connect_serial(self) -> bool:
        try:
            self.serial = Serial(self.serial_port, 115200, timeout=1)
            self.active_connection = 'serial'
            self.log_info("Connected via Serial")
            return True
        except Exception as e:
            self.log_error(f"Serial connection failed: {e}")
            return False

    def connect_wifi(self) -> bool:
        try:
            response = requests.get(f"http://{self.wifi_host}/data")
            if response.status_code == 200:
                self.active_connection = 'wifi'
                self.log_info("Connected via WiFi")
                return True
            return False
        except Exception as e:
            self.log_error(f"WiFi connection failed: {e}")
            return False

    async def connect_bluetooth(self) -> bool:
        try:
            self.ble_client = BleakClient(self.bt_device_name)
            await self.ble_client.connect()
            self.active_connection = 'bluetooth'
            self.log_info("Connected via Bluetooth")
            return True
        except Exception as e:
            self.log_error(f"Bluetooth connection failed: {e}")
            return False

    async def read_data(self) -> Optional[Dict]:
        """Read data from active connection"""
        try:
            if self.active_connection == 'serial':
                return self._read_serial()
            elif self.active_connection == 'wifi':
                return self._read_wifi()
            elif self.active_connection == 'bluetooth':
                return await self._read_bluetooth()
            else:
                self.log_error("No active connection")
                return None
        except Exception as e:
            self.log_error(f"Error reading data: {e}")
            return None

    def _read_serial(self) -> Optional[Dict]:
        if self.serial and self.serial.is_open:
            try:
                data = self.serial.readline().decode('utf-8').strip()
                return eval(data) if data else None
            except Exception as e:
                self.log_error(f"Serial read error: {e}")
        return None

    def _read_wifi(self) -> Optional[Dict]:
        try:
            response = requests.get(f"http://{self.wifi_host}/data")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.log_error(f"WiFi read error: {e}")
            return None

    async def _read_bluetooth(self) -> Optional[Dict]:
        if self.ble_client and self.ble_client.is_connected:
            try:
                data = await self.ble_client.read_gatt_char("181A")
                return eval(data.decode('utf-8'))
            except Exception as e:
                self.log_error(f"Bluetooth read error: {e}")
        return None

    async def disconnect(self):
        """Disconnect active connection"""
        try:
            if self.active_connection == 'serial':
                if self.serial and self.serial.is_open:
                    self.serial.close()
            elif self.active_connection == 'bluetooth':
                if self.ble_client and self.ble_client.is_connected:
                    await self.ble_client.disconnect()
            self.active_connection = None
            self.log_info("Disconnected from device")
        except Exception as e:
            self.log_error(f"Error disconnecting: {e}")
