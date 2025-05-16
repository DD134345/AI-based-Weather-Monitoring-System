import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging

class WeatherDataProcessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='data_processor.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def process_sensor_data(self, data):
        """Process raw sensor data"""
        try:
            if not data:
                return None
                
            # Extract features
            processed_data = {
                'temperature': float(data.get('temperature', 0)),
                'humidity': float(data.get('humidity', 0)),
                'pressure': float(data.get('pressure', 0)),
                'timestamp': data.get('timestamp')
            }
            
            # Basic validation
            if any(value < -100 or value > 100 for key, value in processed_data.items() 
                  if key not in ['pressure', 'timestamp']):
                self.logger.warning(f"Invalid sensor readings detected: {processed_data}")
                return None
                
            self.logger.info(f"Processed data: {processed_data}")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            return None
            
    def prepare_for_prediction(self, data_list, window_size=24):
        """Prepare data for weather prediction"""
        try:
            if not data_list:
                return None
                
            df = pd.DataFrame(data_list)
            
            # Calculate rolling averages
            df['temp_avg_24h'] = df['temperature'].rolling(window=window_size).mean()
            df['humidity_avg_24h'] = df['humidity'].rolling(window=window_size).mean()
            df['pressure_avg_24h'] = df['pressure'].rolling(window=window_size).mean()
            
            # Calculate rate of change
            df['temp_change'] = df['temperature'].diff()
            df['pressure_change'] = df['pressure'].diff()
            
            # Drop NaN values
            df = df.dropna()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error preparing data for prediction: {e}")
            return None