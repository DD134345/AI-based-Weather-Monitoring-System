import asyncio
import logging
from app import BluetoothService

async def test_connection():
    logging.basicConfig(level=logging.INFO)
    service = BluetoothService()
    
    print("Scanning for weather station...")
    connected = await service.connect()
    
    if connected:
        print("Connected! Reading sensor data...")
        data = await service.read_sensor_data()
        print(f"Sensor data: {data}")
        await service.disconnect()
    else:
        print("Failed to connect to weather station")

if __name__ == '__main__':
    asyncio.run(test_connection())