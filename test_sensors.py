from sensor_handler import ArduinoSensorHandler
import time

def test_connection():
    handler = ArduinoSensorHandler()
    
    # List available ports
    print("Available COM ports:")
    ports = handler.list_available_ports()
    for port in ports:
        print(f"- {port.device}: {port.description}")
    
    # Connect to Arduino
    if handler.connect():
        print("Successfully connected to Arduino")
        
        # Read data for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            data = handler.read_sensor_data()
            if data:
                print(f"Received data: {data}")
            time.sleep(1)
            
        handler.close()
    else:
        print("Failed to connect to Arduino")

if __name__ == "__main__":
    test_connection()