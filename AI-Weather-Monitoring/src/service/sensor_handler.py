import asyncio
import json
import logging
from typing import Optional, Dict, Set
from datetime import datetime
import websockets
from bleak import BleakClient
import serial_asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from asyncio import Queue
from collections import deque
import numpy as np

class SensorProtocol(asyncio.Protocol):
    def __init__(self, data_callback):
        super().__init__()
        self.data_callback = data_callback
        self.ready = asyncio.Event()
        self.done = asyncio.Event()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.ready.set()

    def data_received(self, data):
        asyncio.create_task(self.data_callback(data))

    def connection_lost(self, exc):
        self.done.set()

class OptimizedSensorHandler:
    def __init__(self):
        self.data_queue = Queue(maxsize=1000)
        self.data_buffer = deque(maxlen=1000)
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='sensor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self, serial_port: str = 'COM3'):
        """Start all communication channels"""
        try:
            # Start all connections concurrently
            await asyncio.gather(
                self.start_serial(serial_port),
                self.start_ble(),
                self.start_websocket_server(),
                self.start_data_processor()
            )
        except Exception as e:
            self.logger.error(f"Failed to start services: {e}")

    async def start_serial(self, port: str):
        """Start serial connection with automatic reconnection"""
        while True:
            try:
                _, protocol = await serial_asyncio.create_serial_connection(
                    asyncio.get_event_loop(),
                    lambda: SensorProtocol(self.handle_data),
                    port,
                    baudrate=115200
                )
                await protocol.ready.wait()
                self.logger.info(f"Serial connected on {port}")
                await protocol.done.wait()
            except Exception as e:
                self.logger.error(f"Serial connection error: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def start_ble(self):
        """Start BLE connection with automatic reconnection"""
        while True:
            try:
                async with BleakClient("ESP32-Weather") as client:
                    self.logger.info("BLE connected")
                    while True:
                        data = await client.read_gatt_char("181A")
                        await self.handle_data(data)
            except Exception as e:
                self.logger.error(f"BLE connection error: {e}")
                await asyncio.sleep(5)

    async def start_websocket_server(self, host: str = '0.0.0.0', port: int = 8765):
        """Start WebSocket server"""
        async with websockets.serve(self.handle_client, host, port):
            self.logger.info(f"WebSocket server running on {host}:{port}")
            await asyncio.Future()

    async def start_data_processor(self):
        """Process incoming sensor data"""
        while True:
            try:
                data = await self.data_queue.get()
                processed_data = await self.process_data(data)
                if processed_data:
                    self.data_buffer.append(processed_data)
                    await self.broadcast_data(processed_data)
            except Exception as e:
                self.logger.error(f"Data processing error: {e}")

    async def process_data(self, data: Dict) -> Optional[Dict]:
        """Process and validate sensor data"""
        try:
            # Run validation in thread pool
            valid = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.validate_data,
                data
            )
            
            if not valid:
                return None

            # Add timestamp and moving averages
            processed = {
                **data,
                'timestamp': datetime.now().isoformat(),
                'temperature_avg': self.calculate_moving_average('temperature'),
                'humidity_avg': self.calculate_moving_average('humidity'),
                'pressure_avg': self.calculate_moving_average('pressure')
            }
            
            return processed
        except Exception as e:
            self.logger.error(f"Processing error: {e}")
            return None

    def validate_data(self, data: Dict) -> bool:
        """Validate sensor readings"""
        try:
            valid_ranges = {
                'temperature': (-50, 60),
                'humidity': (0, 100),
                'pressure': (900, 1100)
            }
            
            return all(
                key in data and 
                isinstance(data[key], (int, float)) and
                valid_ranges[key][0] <= data[key] <= valid_ranges[key][1]
                for key in valid_ranges
            )
        except Exception:
            return False

    def calculate_moving_average(self, field: str, window: int = 10) -> float:
        """Calculate moving average for a field"""
        try:
            values = [d[field] for d in list(self.data_buffer)[-window:]]
            return float(np.mean(values)) if values else 0
        except Exception:
            return 0

    async def broadcast_data(self, data: Dict):
        """Broadcast data to all connected clients"""
        if not self.connected_clients:
            return
            
        message = json.dumps(data)
        await asyncio.gather(*(
            client.send(message)
            for client in self.connected_clients
        ), return_exceptions=True)

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle WebSocket client connection"""
        self.connected_clients.add(websocket)
        try:
            # Send recent data to new client
            if self.data_buffer:
                recent_data = list(self.data_buffer)[-100:]
                await websocket.send(json.dumps({
                    'type': 'history',
                    'data': recent_data
                }))
            
            async for message in websocket:
                # Handle client messages if needed
                pass
        finally:
            self.connected_clients.remove(websocket)

    async def handle_data(self, data: bytes):
        """Handle incoming sensor data"""
        try:
            decoded = json.loads(data.decode())
            await self.data_queue.put(decoded)
        except Exception as e:
            self.logger.error(f"Data handling error: {e}")