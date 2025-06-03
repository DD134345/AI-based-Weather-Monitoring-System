import os
import subprocess
import sys

def setup_environment():
    """Set up the Python environment"""
    # Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", ".venv"])
    
    # Activate venv and install dependencies
    if os.name == 'nt':  # Windows
        subprocess.run([".venv\\Scripts\\pip", "install", "-e", "."])
    else:  # Linux/Mac
        subprocess.run([".venv/bin/pip", "install", "-e", "."])

    # Create necessary directories
    directories = [
        "logs",
        "models",
        "data",
        "cache",
        "AI-Weather-Monitoring/src/core",
        "AI-Weather-Monitoring/src/connections",
        "AI-Weather-Monitoring/src/utils"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    setup_environment()