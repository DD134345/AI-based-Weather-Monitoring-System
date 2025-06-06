import time
import asyncio
from typing import Dict, Optional
from src.service.sensor_handler import SensorHandler
from src.core.core import WeatherDataProcessor
from src.core.weather_predictor import WeatherPredictor
import logging
import json
from src.service import ConnectionManager

class WeatherController:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.sensor_handler = SensorHandler()
        self.data_processor = WeatherDataProcessor()
        self.predictor = WeatherPredictor()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='controller.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start monitoring weather data"""
        if not self.sensor_handler.connect():
            self.logger.error("Failed to connect to sensors")
            return

        try:
            while True:
                # Read sensor data
                raw_data = self.sensor_handler.read_data()
                if raw_data:
                    # Process data
                    processed_data = self.data_processor.process_sensor_data(raw_data)
                    if processed_data:
                        # Generate prediction if enough data
                        prediction_data = self.data_processor.prepare_for_prediction()
                        if prediction_data is not None:
                            prediction = self.predictor.predict(prediction_data)
                            self.save_current_state(processed_data, prediction)

                await asyncio.sleep(5)  # Wait 5 seconds between readings

        except Exception as e:
            self.logger.error(f"Error in weather monitoring: {e}")
            time.sleep(5)

    def process_data(self, data: dict):
        """Process the received weather data"""
        self.logger.info(f"Received weather data: {data}")
        # Add your data processing logic here

    def save_current_state(self, weather_data: Dict, prediction: Optional[str]):
        """Save current weather state and prediction for mobile app"""
        try:
            state = {
                "current_weather": weather_data,
                "prediction": prediction,
                "timestamp": weather_data['timestamp']
            }
            with open('current_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

class WeatherDataProcessor:
    def process_sensor_data(self, raw_data):
        # Process the sensor data
        return raw_data

    def prepare_for_prediction(self):
        # Prepare data for prediction
        return None