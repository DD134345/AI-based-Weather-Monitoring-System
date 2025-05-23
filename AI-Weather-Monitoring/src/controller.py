import time
from typing import Dict, Optional
from .service.sensor_handler import SensorHandler
from data_processor import WeatherDataProcessor
from .weather_predictor import WeatherPredictor
import logging
import json

class WeatherController:
    def __init__(self):
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

    def start(self):
        """Start the weather monitoring system"""
        if not self.sensor_handler.connect():
            self.logger.error("Failed to connect to sensors")
            return

        while True:
            try:
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

                time.sleep(5)  # Read every 5 seconds

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)

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