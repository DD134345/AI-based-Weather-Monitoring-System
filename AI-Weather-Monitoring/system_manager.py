import asyncio
import logging
from datetime import datetime
import click
from typing import Optional
from config import config
from src.connections.device_manager import DeviceManager
from src.core.weather_predictor import WeatherPredictor

class SystemManager:
    def __init__(self):
        self.setup_logging()
        self.device = DeviceManager()
        self.predictor = WeatherPredictor()
        self.running = False

    def setup_logging(self):
        logging.basicConfig(
            filename=f'logs/system_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.running = True
        try:
            # Try connections in order
            connected = await self._establish_connection()
            if not connected:
                self.logger.error("Failed to connect to weather station")
                return False

            # Start main loop
            while self.running:
                await self._process_cycle()
                await asyncio.sleep(config.get('hardware', 'sensor_update_interval'))

        except Exception as e:
            self.logger.error(f"System error: {e}")
            return False
        finally:
            await self.stop()

    async def _establish_connection(self) -> bool:
        connection_methods = [
            ('wifi', {'ip': config.get('connections', 'wifi_host')}),
            ('bluetooth', {'device_name': config.get('connections', 'bt_device_name')}),
            ('serial', {
                'port': config.get('hardware', 'arduino_port'),
                'baudrate': config.get('hardware', 'baudrate')
            })
        ]

        for method, params in connection_methods:
            self.logger.info(f"Attempting {method} connection...")
            if await self.device.connect(method, **params):
                self.logger.info(f"Connected via {method}")
                return True
        return False

    async def _process_cycle(self):
        try:
            # Read sensor data
            data = await self.device.read_data()
            if not data:
                return

            # Process data and get prediction
            processed = await self.predictor.process_sensor_stream(data)
            if processed:
                predictions = await self.predictor.predict_next_week()
                self.logger.info(f"Current conditions: {processed}")
                self.logger.info(f"Predictions generated: {len(predictions)} intervals")

        except Exception as e:
            self.logger.error(f"Processing error: {e}")

    async def stop(self):
        self.running = False
        await self.device.disconnect()
        self.logger.info("System stopped")

@click.group()
def cli():
    """Weather Monitoring System CLI"""
    pass

@cli.command()
def start():
    """Start the weather monitoring system"""
    manager = SystemManager()
    asyncio.run(manager.start())

@cli.command()
def check():
    """Check system status"""
    manager = SystemManager()
    manager.check_status()

if __name__ == '__main__':
    cli()