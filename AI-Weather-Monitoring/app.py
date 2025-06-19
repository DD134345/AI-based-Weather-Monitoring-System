import asyncio
import logging
import os
import signal
import sys
import winreg
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from src.service.device_manager import DeviceManager  # Updated import
from src.utils.logger import setup_logging
from src.service.service import WeatherService
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np

class WeatherPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
        self.data_buffer = []
        
    def process_sensor_data(self, data: dict) -> dict:
        """Process and predict weather data"""
        try:
            # Validate data
            if not all(key in data for key in ['temperature', 'humidity', 'pressure']):
                raise ValueError("Missing required sensor data")
                
            # Add to buffer
            self.data_buffer.append(data)
            if len(self.data_buffer) > 1000:  # Keep last 1000 readings
                self.data_buffer.pop(0)
                
            # Make prediction
            prediction = self._predict_next_values(data)
            
            return {
                'current': data,
                'prediction': prediction,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return {'current': data, 'prediction': {}, 'error': str(e)}
            
    def _predict_next_values(self, current_data: dict) -> dict:
        """Predict next weather values"""
        try:
            return {
                'temperature': round(current_data['temperature'] + np.random.normal(0, 0.5), 2),
                'humidity': min(100, max(0, round(current_data['humidity'] + np.random.normal(0, 1), 2))),
                'pressure': round(current_data['pressure'] + np.random.normal(0, 0.2), 2),
                'forecast_time': (datetime.now() + timedelta(hours=1)).isoformat()
            }
        except Exception as e:
            logging.error(f"Prediction calculation error: {e}")
            return {}

class WeatherApp:
    def __init__(self):
        self.setup_paths()
        self.setup_environment()
        self.running = True
        self.device = None
        self.service: Optional[WeatherService] = None
        self.reconnect_attempts = 3
        self.reconnect_delay = 5  # seconds
        self.predictor = WeatherPredictor()
        
    def setup_paths(self):
        """Setup Windows-specific paths"""
        self.base_path = Path(__file__).parent
        self.logs_path = self.base_path / 'logs'
        self.data_path = self.base_path / 'data'
        self.config_path = self.base_path / 'config'
        
        # Create necessary directories
        for path in [self.logs_path, self.data_path, self.config_path]:
            path.mkdir(exist_ok=True)

    def setup_environment(self):
        """Setup Windows-specific environment"""
        load_dotenv()
        self.logger = setup_logging(
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=str(self.logs_path / f"weather_station_{datetime.now().strftime('%Y%m%d')}.log")
        )
        
        # Set Windows event loop policy
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def get_com_ports(self):
        """Get available COM ports on Windows"""
        ports = []
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r'HARDWARE\DEVICEMAP\SERIALCOMM')
            for i in range(256):
                try:
                    ports.append(winreg.EnumValue(key, i)[1])
                except OSError:
                    break
        except WindowsError:
            pass
        return ports

    async def connect_device(self):
        """Connect to weather station with improved error handling"""
        self.device = DeviceManager()
        
        connection_methods = [
            ('serial', {'port': port}) for port in self.get_com_ports()
        ] + [
            ('wifi', {'ip': os.getenv('WIFI_HOST', '192.168.4.1')}),
            ('bluetooth', {'device_name': os.getenv('BT_DEVICE_NAME', 'ESP32-Weather')})
        ]
        
        for attempt in range(self.reconnect_attempts):
            for method, params in connection_methods:
                try:
                    self.logger.info(f"Connection attempt {attempt + 1} using {method}")
                    if await self.device.connect(method, **params):
                        self.logger.info(f"Successfully connected via {method}")
                        return True
                except Exception as e:
                    self.logger.warning(f"{method} connection failed: {e}")
                await asyncio.sleep(self.reconnect_delay)
                
        self.logger.error("All connection attempts failed")
        return False

    async def run(self):
        """Enhanced main application loop"""
        try:
            if not await self.connect_device():
                return False

            self.service = WeatherService()
            await self.service.start()

            while self.running:
                try:
                    if self.device is None:
                        if not await self.connect_device():
                            await asyncio.sleep(self.reconnect_delay)
                            continue
                    
                    if self.device:  # Check if device is still connected
                        data = await self.device.read_data()
                    else:
                        continue
                    if data and self.validate_sensor_data(data):
                        result = self.predictor.process_sensor_data(data)
                        await self.service.broadcast_data(result)
                        self.logger.debug(f"Processed data: {result}")
                        
                    await asyncio.sleep(int(os.getenv('UPDATE_INTERVAL', '5')))
                    
                except ConnectionError as e:
                    self.logger.error(f"Connection lost: {e}")
                    self.device = None
                except Exception as e:
                    self.logger.error(f"Processing error: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            self.logger.error(f"System error: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        if self.device:
            await self.device.disconnect()
        if self.service:
            await self.service.stop()

    def signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info("Shutdown signal received")
        self.running = False

    def validate_sensor_data(self, data: dict) -> bool:
        """Validate sensor data"""
        try:
            required_fields = {'temperature', 'humidity', 'pressure'}
            if not all(field in data for field in required_fields):
                self.logger.error(f"Missing required fields: {required_fields - set(data.keys())}")
                return False
                
            valid_ranges = {
                'temperature': (-40, 60),  # Celsius
                'humidity': (0, 100),      # Percentage
                'pressure': (900, 1100)    # hPa
            }
            
            for field, (min_val, max_val) in valid_ranges.items():
                if not min_val <= data[field] <= max_val:
                    self.logger.warning(f"Invalid {field}: {data[field]}")
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Data validation error: {e}")
            return False

async def main():
    app = WeatherApp()
    
    # Setup signal handlers for Windows
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)
    
    await app.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        sys.exit(0)