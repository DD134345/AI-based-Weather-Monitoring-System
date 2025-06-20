import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
import websockets
import websockets.legacy
from websockets.legacy.server import WebSocketServerProtocol
from collections import deque

import websockets.legacy.server

class SimpleSensorHandler:
    def __init__(self):
        self.data_buffer = deque(maxlen=100)  # Reduced buffer size
        self.connected_clients: Set[websockets.legacy.server.WebSocketServerProtocol] = set()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self, serial_port: str = 'COM3'):
        """Start the main service"""
        try:
            await asyncio.gather(
                self.start_serial(serial_port),
                self.start_websocket_server()
            )
        except Exception as e:
            self.logger.error(f"Service start failed: {e}")

    async def start_serial(self, port: str):
        """Simple serial connection handler"""
        import serial_asyncio
        
        while True:
            try:
                reader, _ = await serial_asyncio.open_serial_connection(
                    url=port,
                    baudrate=115200
                )
                while True:
                    data = await reader.readline()
                    await self.handle_data(data)
            except Exception as e:
                self.logger.error(f"Serial error: {e}")
                await asyncio.sleep(5)

    async def start_websocket_server(self, port: int = 8765):
        """Simple WebSocket server"""
        async with websockets.legacy.server.serve(self.handle_client, 'localhost', port):
            self.logger.info(f"WebSocket server running on port {port}")
            await asyncio.Future()

    def validate_data(self, data: Dict) -> bool:
        """Basic data validation"""
        try:
            return all(
                isinstance(data.get(key), (int, float))
                for key in ['temperature', 'humidity', 'pressure']
            )
        except Exception:
            return False

    async def handle_data(self, raw_data: bytes):
        """Process incoming data"""
        try:
            data = json.loads(raw_data.decode('utf-8').strip())
            if self.validate_data(data):
                data['timestamp'] = datetime.now().isoformat()
                self.data_buffer.append(data)
                await self.broadcast_data(data)
        except Exception as e:
            self.logger.error(f"Data handling error: {e}")

    async def broadcast_data(self, data: Dict):
        """Send data to all connected clients"""
        if not self.connected_clients:
            return
            
        message = json.dumps(data)
        for client in self.connected_clients.copy():
            try:
                await client.send(message)
            except Exception:
                self.connected_clients.remove(client)

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle client connection"""
        self.connected_clients.add(websocket)
        try:
            if self.data_buffer:
                await websocket.send(json.dumps({
                    'type': 'history',
                    'data': list(self.data_buffer)
                }))
            async for _ in websocket:
                pass  # Just keep connection alive
        finally:
            self.connected_clients.remove(websocket)