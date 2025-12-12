"""MongoDB integration"""

import logging
from datetime import datetime
from pymongo import MongoClient

from src.config import (
    MONGO_URI, MONGO_DB_NAME, MONGO_ENRICHED_CONTACTS_COLLECTION, CONTINUE_ON_ERROR
)

logger = logging.getLogger(__name__)


class MongoDBService:
    """MongoDB integration for storing enriched contacts"""

    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Test connection
            self.db = self.client[MONGO_DB_NAME]
            self.enriched_col = self.db[MONGO_ENRICHED_CONTACTS_COLLECTION]
            logger.info("✓ MongoDB connected")
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {e}")
            if not CONTINUE_ON_ERROR:
                raise

    def store_enriched_contact(self, contact: dict) -> bool:
        """Store enriched contact in MongoDB"""
        try:
            contact['stored_at'] = datetime.utcnow()
            self.enriched_col.insert_one(contact)
            return True
        except Exception as e:
            logger.warning(f"✗ Error storing contact: {e}")
            if not CONTINUE_ON_ERROR:
                raise
            return False

    def store_batch(self, contacts: list[dict]) -> bool:
        """Store batch of enriched contacts"""
        try:
            if not contacts:
                return True
            for contact in contacts:
                contact['stored_at'] = datetime.utcnow()
            self.enriched_col.insert_many(contacts)
            logger.info(f"✓ Stored {len(contacts)} contacts in MongoDB")
            return True
        except Exception as e:
            logger.warning(f"✗ Error storing batch: {e}")
            if not CONTINUE_ON_ERROR:
                raise
            return False

    def close(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            logger.info("✓ MongoDB connection closed")
        except Exception as e:
            logger.warning(f"Issue closing MongoDB: {e}")
