"""
Logging configuration for GitHub Contribution Hack

Configures loggers for various modules with appropriate handlers
and formatters. Supports both console and file-based logging
with different levels for development and production environments.
"""
import os
import logging
import logging.handlers
from datetime import datetime

def configure_logging(log_level=None, log_file=None):
    """
    Configure logging system for the entire application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, None for no file logging
    """
    if log_level is None:
        # Default to INFO in production, DEBUG in development
        log_level = os.environ.get("LOG_LEVEL", "INFO")
    
    # Convert string to logging level constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Base configuration
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': numeric_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout',
            },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': True
            },
            'mcp_integration': {
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': False
            },
            'main': {
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': False
            },
            'analytics': {
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': False
            }
        }
    }
    
    # Add file handler if log_file is specified
    if log_file:
        log_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': numeric_level,
            'formatter': 'detailed',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
        
        # Add file handler to all loggers
        for logger_name in log_config['loggers']:
            log_config['loggers'][logger_name]['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(log_config)
    
    # Log startup message
    logging.info(f"Logging system initialized at {datetime.now().isoformat()}")
    logging.info(f"Log level: {log_level}")
    if log_file:
        logging.info(f"Log file: {log_file}")

def get_logger(name):
    """Get a configured logger for a module"""
    return logging.getLogger(name) 