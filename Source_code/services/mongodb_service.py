"""
MongoDB service layer
"""

from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from Source_code.utils.logger import logger
from Source_code.config import config


class MongoDBService:
    """Service for MongoDB operations"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(config.MONGO_HOST)
            self.db = self.client[config.MONGO_DATABASE]
            self.collection = self.db[config.MONGO_COLLECTION]

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {config.MONGO_DATABASE}.{config.MONGO_COLLECTION}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_all_emails(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get all emails from MongoDB"""
        try:
            cursor = self.collection.find()
            if limit:
                cursor = cursor.limit(limit)

            emails = list(cursor)
            logger.info(f"Retrieved {len(emails)} emails from MongoDB")
            return emails

        except Exception as e:
            logger.error(f"Failed to get emails: {e}")
            return []

    def get_emails_batch(self, skip: int = 0, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Get emails in batches for efficient processing"""
        try:
            emails = list(self.collection.find().skip(skip).limit(batch_size))
            return emails
        except Exception as e:
            logger.error(f"Failed to get batch: {e}")
            return []

    def get_total_count(self) -> int:
        """Get total number of emails"""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            return 0

    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find emails by criteria - CUSTOMIZE for your team's schema"""
        try:
            # Example criteria - ADJUST THESE based on your database!
            query = {}

            if 'from_email' in criteria:
                query['from'] = {'$regex': criteria['from_email'], '$options': 'i'}
            if 'date_from' in criteria:
                query['date'] = {'$gte': criteria['date_from']}
            if 'date_to' in criteria and 'date' in query:
                query['date']['$lte'] = criteria['date_to']
            elif 'date_to' in criteria:
                query['date'] = {'$lte': criteria['date_to']}
            if 'has_attachment' in criteria:
                query['has_attachment'] = criteria['has_attachment']

            return list(self.collection.find(query))

        except Exception as e:
            logger.error(f"Failed to find by criteria: {e}")
            return []

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")