import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import click
import json
import requests
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from dotenv import load_dotenv
import joblib
from bleak import BleakClient, BleakScanner
import serial
from concurrent.futures import ThreadPoolExecutor

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
                },
                'api': {
                    'key': os.getenv('OPENWEATHER_API_KEY'),
                    'cache_duration': 300  # 5 minutes
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

# Enhanced Weather System Manager
class EnhancedWeatherSystem:
    def __init__(self):
        self.setup_config()
        self.setup_logging()
        self.setup_models()
        self.data_buffer = []
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.device = DeviceManager()
        self.running = False
        self.short_term_buffer = []  # For 5-second intervals
        self.long_term_buffer = []   # For daily predictions
        self.last_short_prediction = None
        self.last_long_prediction = None

    def setup_config(self):
        load_dotenv()
        self.config = {
            'hardware': {
                'arduino_port': os.getenv('ARDUINO_PORT', 'COM3'),
                'baudrate': int(os.getenv('BAUDRATE', '115200')),
                'sensor_update_interval': int(os.getenv('SENSOR_UPDATE_INTERVAL', '5'))
            },
            'model': {
                'path': os.getenv('MODEL_PATH', 'models/weather_model.joblib'),
                'buffer_size': int(os.getenv('BUFFER_SIZE', '1000')),
                'min_samples': 24 * 7  # 7 days minimum
            },
            'api': {
                'key': os.getenv('OPENWEATHER_API_KEY'),
                'cache_duration': 300  # 5 minutes
            }
        }

    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename=f'logs/system_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_models(self):
        self.model = self._load_model() or RandomForestRegressor(
            n_estimators=500,
            max_depth=15,
            min_samples_split=5,
            n_jobs=-1,
            random_state=42
        )
        self.scaler = RobustScaler()

    def _load_model(self) -> Optional[RandomForestRegressor]:
        try:
            if os.path.exists(self.config['model']['path']):
                return joblib.load(self.config['model']['path'])
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
        return None

    def save_model(self):
        try:
            os.makedirs(os.path.dirname(self.config['model']['path']), exist_ok=True)
            joblib.dump(self.model, self.config['model']['path'])
            self.logger.info("Model saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")

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
                timestamp = datetime.now()
                processed_data = {
                    'temperature': float(data['temperature']),
                    'humidity': float(data['humidity']),
                    'pressure': float(data['pressure']),
                    'timestamp': timestamp.isoformat()
                }

                # Update both buffers
                self.short_term_buffer.append(processed_data)
                if len(self.short_term_buffer) > 720:  # Last hour (12 samples/minute)
                    self.short_term_buffer.pop(0)

                # Add to long-term buffer every hour
                if len(self.long_term_buffer) == 0 or \
                   (timestamp - datetime.fromisoformat(self.long_term_buffer[-1]['timestamp'])).seconds >= 3600:
                    self.long_term_buffer.append(processed_data)
                    if len(self.long_term_buffer) > 24 * 30:  # 30 days of hourly data
                        self.long_term_buffer.pop(0)

                # Generate predictions
                await self._generate_predictions(timestamp)
                
                self.logger.info(f"Current conditions: {processed_data}")
                
        except Exception as e:
            self.logger.error(f"Processing error: {e}")

    async def _generate_predictions(self, timestamp: datetime):
        try:
            # Long-term prediction (7 days) after collecting 7 days of data
            if len(self.long_term_buffer) >= 24 * 7:
                hours_since_last = float('inf') if not self.last_long_prediction else \
                    (timestamp - self.last_long_prediction).total_seconds() / 3600
                
                if hours_since_last >= 6:  # Update every 6 hours
                    predictions = await self.predict_weather(days_ahead=7)
                    self.logger.info(f"7-day forecast updated: {predictions}")
                    self.last_long_prediction = timestamp

            # Short-term prediction (24 hours) using recent data
            if len(self.short_term_buffer) >= 720:  # At least 1 hour of data
                minutes_since_last = float('inf') if not self.last_short_prediction else \
                    (timestamp - self.last_short_prediction).total_seconds() / 60
                
                if minutes_since_last >= 5:  # Update every 5 minutes
                    prediction = await self._predict_short_term()
                    self.logger.info(f"24-hour forecast updated: {prediction}")
                    self.last_short_prediction = timestamp

        except Exception as e:
            self.logger.error(f"Prediction generation error: {e}")

    async def _predict_short_term(self) -> Dict:
        """Generate 24-hour prediction using recent high-frequency data"""
        try:
            # Prepare recent data
            recent_data = pd.DataFrame(self.short_term_buffer)
            recent_data['datetime'] = pd.to_datetime(recent_data['timestamp'])
            
            # Calculate rolling averages and trends
            for column in ['temperature', 'humidity', 'pressure']:
                recent_data[f'{column}_trend'] = recent_data[column].diff(periods=12)  # 1-minute trend
                recent_data[f'{column}_avg_5min'] = recent_data[column].rolling(window=60).mean()
                recent_data[f'{column}_std_5min'] = recent_data[column].rolling(window=60).std()

            # Make prediction
            features = recent_data.iloc[-1:][['temperature', 'humidity', 'pressure',
                                            'temperature_trend', 'humidity_trend', 'pressure_trend',
                                            'temperature_avg_5min', 'humidity_avg_5min', 'pressure_avg_5min',
                                            'temperature_std_5min', 'humidity_std_5min', 'pressure_std_5min']]
            
            prediction = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self.model.predict,
                features
            )

            return {
                'timestamp': (datetime.now() + timedelta(hours=24)).isoformat(),
                'temperature': float(prediction[0][0]),
                'humidity': float(prediction[0][1]),
                'pressure': float(prediction[0][2]),
                'condition': self._determine_weather_type(
                    prediction[0][0],
                    prediction[0][1],
                    prediction[0][2]
                ),
                'confidence': self._calculate_confidence(prediction[0])
            }

        except Exception as e:
            self.logger.error(f"Short-term prediction error: {e}")
            return None

    def validate_data(self, data: Dict) -> bool:
        """Validate sensor readings"""
        try:
            required_fields = {'temperature', 'humidity', 'pressure'}
            if not all(field in data for field in required_fields):
                return False

            valid_ranges = {
                'temperature': (-40, 80),
                'humidity': (0, 100),
                'pressure': (900, 1100)
            }

            return all(
                valid_ranges[field][0] <= data[field] <= valid_ranges[field][1]
                for field in required_fields
            )
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

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

# Weather Predictor
class WeatherPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()

    async def predict_weather(self, data_buffer):
        # Process historical data for prediction
        X = np.array([[d['temperature'], d['humidity'], d['pressure']] for d in data_buffer])
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model on recent data
        X_train = X_scaled[:-1]
        y_train = X_scaled[1:]
        self.model.fit(X_train, y_train)
        
        # Make prediction
        return self.model.predict(X_scaled[-1:].reshape(1, -1))

# Weather System Manager
class WeatherSystem:
    def __init__(self):
        self.setup_logging()
        self.config = Config()
        self.device = DeviceManager()
        self.scaler = StandardScaler()
        self.data_buffer = []
        self.running = False
        self.predictor = WeatherPredictor()
        
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
                
                # Keep 30 days of data for better predictions
                if len(self.data_buffer) > 24 * 30:
                    self.data_buffer.pop(0)
                
                # Generate prediction every 6 hours
                if len(self.data_buffer) >= 24 * 7 and len(self.data_buffer) % 6 == 0:
                    predictions = await self.predictor.predict_weather(self.data_buffer)
                    self.logger.info(f"Updated weather predictions: {predictions}")
                
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