"""Configuration settings for the POS system."""

import os
import json
import logging
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Configuration file path
CONFIG_FILE = BASE_DIR / 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    'db': {
        'host': 'localhost',
        'port': 3306,
        'database': 'pos_db',
        'user': 'root',
        'password': '9899',
    },
    'app': {
        'name': 'Infoware POS',
        'version': '1.0.0',
        'log_level': 'INFO',
        'theme': 'light',
    }
}


def get_config():
    """
    Load configuration from file or create default if it doesn't exist.
    Returns the configuration dictionary.
    """
    if not CONFIG_FILE.exists():
        # Create default config file if it doesn't exist
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG


# Configure logging
def setup_logging():
    """Set up logging for the application."""
    config = get_config()
    log_level = getattr(logging, config['app']['log_level'])
    
    # Create logs directory if it doesn't exist
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'pos.log'),
            logging.StreamHandler()
        ]
    )