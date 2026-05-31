"""
Centralized logging configuration
"""

import logging
import os
from datetime import datetime

class Logger:
    """Custom logger with file and console output"""

    _instances = {}

    def __new__(cls, name='PersianSearch'):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
            cls._instances[name]._setup_logger(name)
        return cls._instances[name]

    def _setup_logger(self, name):
        """Setup logger with handlers"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Get the project root directory (where .env is located)
        current_file = os.path.abspath(__file__)
        # Go up from Source_code/utils/logger.py to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        # Use LOG_DIR from .env if available, otherwise default to 'logs'
        log_dir_name = 'logs'
        try:
            from Source_code.config import config
            log_dir_name = getattr(config, 'LOG_DIR', 'logs')
        except ImportError:
            # If config not available, use default
            pass

        # Create logs directory in project root
        log_dir = os.path.join(project_root, log_dir_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create log file path
        log_file = os.path.join(log_dir, f'persian_search_{datetime.now().strftime("%Y%m%d")}.log')

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"Log file created at: {log_file}")

    def get_logger(self):
        return self.logger


# Global logger instance
logger = Logger().get_logger()