"""
Shared Logging Configuration
Centralized logging setup for all services.
"""
import logging
import sys


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger for the service.
    
    Args:
        service_name: Name of the service (e.g., "skill-service").
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    
    Returns:
        logging.Logger: Configured logger.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return logger
