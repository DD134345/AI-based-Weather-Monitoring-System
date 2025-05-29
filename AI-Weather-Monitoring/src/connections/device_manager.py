import asyncio
import logging
from typing import Optional, Dict
import serial
import aiohttp
from bleak import BleakClient, BleakScanner
import json

class DeviceManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_type = None
        self.serial_conn = None
        self.ble_client = None
        self.wifi_url = None
        
    async def connect(self, connection_type: str, **kwargs) -> bool:
        """Connect to device using specified method"""
        self.connection_type = connection_type
        
        try:
            if connection_type == 'serial':
                return self._connect_serial(
                    port=kwargs.get('port', 'COM3'),
                    baudrate=kwargs.get('baudrate', 115200)
                )
            elif connection_type == 'bluetooth':
                return await self._connect_bluetooth(
                    device_name=kwargs.get('device_name', 'ESP32-Weather')
                )
            elif connection_type == 'wifi':
                return await self._connect_wifi(
                    ip=kwargs.get('ip', '192.168.4.1')
                )
            else:
                self.logger.error(f"Unsupported connection type: {connection_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def _connect_serial(self, port: str, baudrate: int) -> bool:
        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            self.logger.info(f"Serial connected on {port}")
            return True
        except Exception as e:
            self.logger.error(f"Serial connection failed: {e}")
            return False

    async def _connect_bluetooth(self, device_name: str) -> bool:
        try:
            device = await BleakScanner.find_device_by_name(device_name)
            if not device:
                self.logger.error("Bluetooth device not found")
                return False
                
            self.ble_client = BleakClient(device.address)
            await self.ble_client.connect()
            self.logger.info(f"Bluetooth connected to {device_name}")
            return True
        except Exception as e:
            self.logger.error(f"Bluetooth connection failed: {e}")
            return False

    async def _connect_wifi(self, ip: str) -> bool:
        try:
            self.wifi_url = f"http://{ip}/data"
            async with aiohttp.ClientSession() as session:
                async with session.get(self.wifi_url) as response:
                    if response.status == 200:
                        self.logger.info(f"WiFi connected to {ip}")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"WiFi connection failed: {e}")
            return False

    async def read_data(self) -> Optional[Dict]:
        """Read sensor data using active connection"""
        try:
            if self.connection_type == 'serial':
                return await self._read_serial()
            elif self.connection_type == 'bluetooth':
                return await self._read_bluetooth()
            elif self.connection_type == 'wifi':
                return await self._read_wifi()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            return None

    async def _read_serial(self) -> Optional[Dict]:
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
            
        if self.serial_conn.in_waiting:
            data = self.serial_conn.readline().decode('utf-8').strip()
            return json.loads(data)
        return None

    async def _read_bluetooth(self) -> Optional[Dict]:
        if not self.ble_client or not self.ble_client.is_connected:
            return None
            
        data = await self.ble_client.read_gatt_char("181A")
        return json.loads(data.decode('utf-8'))

    async def _read_wifi(self) -> Optional[Dict]:
        if not self.wifi_url:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.get(self.wifi_url) as response:
                if response.status == 200:
                    return await response.json()
        return None

    async def disconnect(self):
        """Disconnect active connection"""
        try:
            if self.connection_type == 'serial':
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
            elif self.connection_type == 'bluetooth':
                if self.ble_client and self.ble_client.is_connected:
                    await self.ble_client.disconnect()
            self.connection_type = None
            self.logger.info("Disconnected from device")
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")