import os
import subprocess
import sys
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def setup_environment():
    """Set up the Python environment"""
    try:
        # Create virtual environment
        logging.info("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        
        # Activate venv and install dependencies
        logging.info("Installing dependencies...")
        if os.name == 'nt':  # Windows
            subprocess.run([".venv\\Scripts\\pip", "install", "-e", "."], check=True)
        else:  # Linux/Mac
            subprocess.run([".venv/bin/pip", "install", "-e", "."], check=True)

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
        
        logging.info("Creating directory structure...")
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        logging.info("Setup completed successfully!")
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during dependency installation: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    setup_environment()