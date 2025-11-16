import logging
import sys

def get_logger(name: str):
    """
        Initializes and returns a logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers: # Avoid adding handlers multiple times
        logger.setLevel(logging.DEBUG)
        
        # Create a handler to print to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        # Create a formatter and add it to the handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(handler)
        
    return logger
