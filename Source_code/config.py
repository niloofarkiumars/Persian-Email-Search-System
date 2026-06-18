"""
Configuration management with environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""

    # Elasticsearch
    ES_HOST = os.getenv('ES_HOST', 'https://localhost:9200')
    ES_USERNAME = os.getenv('ES_USERNAME', 'elastic')
    ES_PASSWORD = os.getenv('ES_PASSWORD', '')

    # MongoDB
    MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb://localhost:27017/')
    MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'email_db')
    MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'emails')

    # Application
    INDEX_NAME = os.getenv('INDEX_NAME', 'persian_emails')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
    LOG_DIR = os.getenv('LOG_DIR', 'logs')  # Add this line
    SEMANTIC_VECTOR_DIMS = int(os.getenv('SEMANTIC_VECTOR_DIMS', '384'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ES_PASSWORD:
            raise ValueError("ES_PASSWORD is required! Please set it in .env file")
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    LOG_LEVEL = 'WARNING'

# Select configuration based on environment
ENV = os.getenv('ENV', 'development')
if ENV == 'production':
    config = ProductionConfig()
else:
    config = DevelopmentConfig()
