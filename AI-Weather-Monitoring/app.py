import asyncio
from datetime import datetime
from src.connections.device_manager import DeviceManager
from src.core.weather_predictor import WeatherPredictor
from src.utils.logger import setup_logging

async def main():
    # Setup logging with file output
    logger = setup_logging(
        log_level="INFO",
        log_file=f"weather_station_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    device = DeviceManager()
    predictor = WeatherPredictor()
    
    # Try connection methods in order
    connection_methods = [
        ('serial', {'port': 'COM3'}),
        ('bluetooth', {'device_name': 'ESP32-Weather'}),
        ('wifi', {'ip': '192.168.4.1'})
    ]
    
    connected = False
    for method, params in connection_methods:
        logger.info(f"Trying {method} connection...")
        if await device.connect(method, **params):
            connected = True
            break
            
    if not connected:
        logger.error("Failed to connect to device")
        return
        
    try:
        logger.info("Started weather monitoring")
        while True:
            data = await device.read_data()
            if data:
                processed = predictor.process_sensor_data(data)
                if processed:
                    prediction = predictor.predict_weather(processed)
                    logger.info(f"Weather data: {processed}")
                    logger.info(f"Prediction: {prediction}")
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Shutting down")
        await device.disconnect()
    except Exception as e:
        logger.error(f"Error: {e}")
        await device.disconnect()

if __name__ == '__main__':
    asyncio.run(main())