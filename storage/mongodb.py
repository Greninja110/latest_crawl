"""
MongoDB connector for storing raw and processed data
"""
import logging
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from config.settings import (
    MONGODB_URI, 
    MONGODB_DB_NAME, 
    MONGODB_RAW_COLLECTION, 
    MONGODB_PROCESSED_COLLECTION
)

logger = logging.getLogger(__name__)

class MongoDBConnector:
    """MongoDB connector for the crawler system"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[MONGODB_DB_NAME]
            self.raw_collection = self.db[MONGODB_RAW_COLLECTION]
            self.processed_collection = self.db[MONGODB_PROCESSED_COLLECTION]
            logger.info(f"Connected to MongoDB: {MONGODB_DB_NAME}")
            
            # Create indexes for faster queries
            self._create_indexes()
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for faster queries"""
        # Raw data indexes
        self.raw_collection.create_index("college_name")
        self.raw_collection.create_index("url")
        self.raw_collection.create_index([("page_type", 1), ("college_name", 1)])
        
        # Processed data indexes
        self.processed_collection.create_index("college_name")
        self.processed_collection.create_index("raw_data_id")
        self.processed_collection.create_index([("college_name", 1), ("last_updated", -1)])
    
    def insert_raw_data(self, data: Dict[str, Any]) -> str:
        """
        Insert raw data into the raw_collection
        
        Args:
            data: Dictionary containing raw scraped data
            
        Returns:
            str: ID of the inserted document
        """
        try:
            result = self.raw_collection.insert_one(data)
            logger.debug(f"Inserted raw data with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to insert raw data: {e}")
            raise
    
    def insert_raw_data_batch(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple raw data documents in batch
        
        Args:
            data_list: List of dictionaries containing raw scraped data
            
        Returns:
            List[str]: List of inserted document IDs
        """
        try:
            result = self.raw_collection.insert_many(data_list)
            inserted_ids = [str(id) for id in result.inserted_ids]
            logger.debug(f"Inserted {len(inserted_ids)} raw data documents")
            return inserted_ids
        except PyMongoError as e:
            logger.error(f"Failed to insert raw data batch: {e}")
            raise
    
    def insert_processed_data(self, data: Dict[str, Any]) -> str:
        """
        Insert processed data into the processed_collection
        
        Args:
            data: Dictionary containing processed data
            
        Returns:
            str: ID of the inserted document
        """
        try:
            result = self.processed_collection.insert_one(data)
            logger.debug(f"Inserted processed data with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to insert processed data: {e}")
            raise
    
    def update_processed_data(self, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Update processed data in the processed_collection
        
        Args:
            query: Query to identify the document to update
            data: Data to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            result = self.processed_collection.update_one(query, {"$set": data})
            logger.debug(f"Updated {result.modified_count} processed data document(s)")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update processed data: {e}")
            raise
    
    def get_raw_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get raw data from raw_collection based on query
        
        Args:
            query: Query to filter documents
            
        Returns:
            List[Dict[str, Any]]: List of matching raw data documents
        """
        try:
            return list(self.raw_collection.find(query))
        except PyMongoError as e:
            logger.error(f"Failed to get raw data: {e}")
            raise
    
    def get_processed_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get processed data from processed_collection based on query
        
        Args:
            query: Query to filter documents
            
        Returns:
            List[Dict[str, Any]]: List of matching processed data documents
        """
        try:
            return list(self.processed_collection.find(query))
        except PyMongoError as e:
            logger.error(f"Failed to get processed data: {e}")
            raise
            
    def get_college_data(self, college_name: str, data_type: str) -> Dict[str, Any]:
        """
        Get the latest processed data for a specific college and data type
        
        Args:
            college_name: Name of the college
            data_type: Type of data ('admission' or 'placement')
            
        Returns:
            Dict[str, Any]: The latest processed data or None if not found
        """
        try:
            result = self.processed_collection.find_one(
                {"college_name": college_name, data_type: {"$exists": True}},
                sort=[("last_updated", -1)]
            )
            return result
        except PyMongoError as e:
            logger.error(f"Failed to get college {data_type} data: {e}")
            raise
            
    def url_exists(self, url: str) -> bool:
        """
        Check if a URL already exists in the raw_collection
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL exists, False otherwise
        """
        try:
            return self.raw_collection.count_documents({"url": url}) > 0
        except PyMongoError as e:
            logger.error(f"Failed to check if URL exists: {e}")
            raise

    def close(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB connection closed")