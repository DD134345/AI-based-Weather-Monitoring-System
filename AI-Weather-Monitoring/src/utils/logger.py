import logging
import os
from datetime import datetime
from typing import Optional

def setup_logging(log_level: str = "INFO", 
                 log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging to file
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if logging to file
    if log_file:
        os.makedirs('logs', exist_ok=True)
        if not log_file.startswith('logs/'):
            log_file = f'logs/{log_file}'
            
    # Set up logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        filename=log_file
    )

    # Create console handler if not logging to file
    if not log_file:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.getLogger().addHandler(console_handler)

    return logging.getLogger('WeatherStation')

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Name for the logger
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(f'WeatherStation.{name}')

class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
    def log_error(self, message: str, exc: Optional[Exception] = None):
        """Log an error message with optional exception details"""
        if exc:
            self.logger.error(f"{message}: {str(exc)}")
        else:
            self.logger.error(message)
            
    def log_info(self, message: str):
        """Log an info message"""
        self.logger.info(message)
        
    def log_debug(self, message: str):
        """Log a debug message"""
        self.logger.debug(message)