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
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

if __name__ == "__main__":
    setup_environment()