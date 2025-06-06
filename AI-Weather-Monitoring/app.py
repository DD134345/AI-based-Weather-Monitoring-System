import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from weather_system import DeviceManager
from src.core.weather_predictor import WeatherPredictor
from src.utils.logger import setup_logging
from src.service.service import WeatherService
import logging
import sys

async def main():
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        log_file=f"logs/weather_station_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    # Initialize components
    device = DeviceManager()
    predictor = WeatherPredictor()
    
    # Try connection methods in order of preference
    connection_methods = [
        ('wifi', {'ip': os.getenv('WIFI_HOST', '192.168.4.1')}),
        ('bluetooth', {'device_name': os.getenv('BT_DEVICE_NAME', 'ESP32-Weather')}),
        ('serial', {'port': os.getenv('ARDUINO_PORT', 'COM3')})
    ]
    
    connected = False
    for method, params in connection_methods:
        logger.info(f"Attempting {method} connection...")
        if await device.connect(method, **params):
            connected = True
            logger.info(f"Connected via {method}")
            break
            
    if not connected:
        logger.error("Failed to connect to weather station")
        return

    try:
        logger.info("Starting weather monitoring")
        while True:
            # Read sensor data
            data = await device.read_data()
            if data:
                # Process data and get prediction
                result = predictor.process_sensor_data(data)
                if result:
                    logger.info(f"Current: {result['current']}")
                    logger.info(f"Prediction: {result['prediction']}")
                    
            await asyncio.sleep(int(os.getenv('UPDATE_INTERVAL', '5')))
            
    except KeyboardInterrupt:
        logger.info("Shutting down")
        await device.disconnect()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        await device.disconnect()
    try:
        service = WeatherService()
        await service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"System failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())