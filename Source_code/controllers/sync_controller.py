"""
Sync controller - handles data synchronization
"""

from typing import List, Dict, Any
from tqdm import tqdm
from Source_code.services.elasticsearch_service import ElasticsearchService
from Source_code.services.mongodb_service import MongoDBService
from Source_code.models.email_model import Email, EmailMapper
from Source_code.utils.logger import logger
from Source_code.config import config


class SyncController:
    """Controller for sync operations"""

    def __init__(self):
        self.es_service = ElasticsearchService()
        self.mongo_service = MongoDBService()

    def sync_all(self, force_recreate_index: bool = False) -> Dict[str, Any]:
        """Sync all emails from MongoDB to Elasticsearch"""
        logger.info("Starting full sync from MongoDB to Elasticsearch")

        # Create index
        self.es_service.create_index(force=force_recreate_index)

        # Get emails from MongoDB
        emails = self.mongo_service.get_all_emails()
        total = len(emails)

        if total == 0:
            logger.warning("No emails found in MongoDB")
            return {'synced': 0, 'total': 0}

        # Prepare documents for bulk indexing
        documents = []
        failed = []

        for email_doc in tqdm(emails, desc="Processing emails"):
            try:
                # Map database fields to application model
                mapped = EmailMapper.map_from_db(email_doc)

                # Create Email object
                email = Email(
                    message_id=str(email_doc.get('_id')),
                    subject=mapped.get('subject', ''),
                    body=mapped.get('body', ''),
                    from_address=mapped.get('from_address', ''),
                    to_addresses=mapped.get('to_addresses', []),
                    date=mapped.get('date'),
                    has_attachment=mapped.get('has_attachment', False)
                )

                # Convert to Elasticsearch document
                es_doc = email.to_elasticsearch()
                documents.append((str(email_doc['_id']), es_doc))

            except Exception as e:
                logger.error(f"Failed to process email {email_doc.get('_id')}: {e}")
                failed.append(str(email_doc.get('_id')))

        # Bulk index to Elasticsearch
        synced = self.es_service.bulk_index(documents)

        result = {
            'synced': synced,
            'total': total,
            'failed': len(failed),
            'failed_ids': failed[:10]  # First 10 failed IDs
        }

        logger.info(f"Sync completed: {synced}/{total} emails synced")
        return result

    def sync_incremental(self, last_sync_date) -> Dict[str, Any]:
        """
        Sync only new emails since last sync
        CUSTOMIZE this based on your team's date field name
        """
        # This is a placeholder - customize based on your database schema
        logger.info("Incremental sync not implemented - customize based on your date field")
        return {'synced': 0, 'message': 'Customize the date field in your database'}

    def get_status(self) -> Dict[str, Any]:
        """Get sync status and statistics"""
        es_stats = self.es_service.get_stats()
        mongo_count = self.mongo_service.get_total_count()

        return {
            'elasticsearch': es_stats,
            'mongodb': {
                'document_count': mongo_count
            },
            'sync_percentage': round(es_stats.get('document_count', 0) / max(mongo_count, 1) * 100,
                                     2) if mongo_count > 0 else 0
        }