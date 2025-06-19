import subprocess
import sys
from pathlib import Path

def setup_windows():
    """Setup the application for Windows"""
    print("Setting up Weather Monitoring System for Windows...")
    
    # Install requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Create necessary directories
    dirs = ['logs', 'data', 'models', 'config']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write("""
LOG_LEVEL=INFO
WIFI_HOST=192.168.4.1
BT_DEVICE_NAME=ESP32-Weather
UPDATE_INTERVAL=5
            """.strip())
    
    print("Setup complete! Run 'python app.py' to start the application.")

if __name__ == '__main__':
    setup_windows()