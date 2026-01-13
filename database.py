"""
MongoDB database connection and utilities.
"""

import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional


class MongoDBConnection:
    """Manages MongoDB connection and provides database access."""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "testudo_ai"):
        """
        Initialize MongoDB connection.
        
        Args:
            uri: MongoDB connection URI. If None, reads from MONGODB_URI env var.
            db_name: Name of the database to use
        """
        self.uri = uri or os.getenv("MONGODB_URI")
        if not self.uri:
            raise ValueError("MongoDB URI not provided. Set MONGODB_URI environment variable or pass uri parameter.")
        
        self.db_name = db_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
    
    def connect(self) -> Database:
        """Connect to MongoDB and return the database instance."""
        if self.client is None:
            self.client = MongoClient(self.uri)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print(f"✓ Connected to MongoDB database: {self.db_name}")
        return self.db
    
    def disconnect(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("✓ Disconnected from MongoDB")
    
    def get_database(self) -> Database:
        """Get the database instance, connecting if necessary."""
        if self.db is None:
            return self.connect()
        return self.db
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Global connection instance
_connection: Optional[MongoDBConnection] = None


def get_db_connection(uri: Optional[str] = None, db_name: str = "testudo_ai") -> MongoDBConnection:
    """
    Get or create a global MongoDB connection.
    
    Args:
        uri: MongoDB connection URI (optional, uses env var if not provided)
        db_name: Database name (default: testudo_ai)
        
    Returns:
        MongoDBConnection instance
    """
    global _connection
    if _connection is None:
        _connection = MongoDBConnection(uri, db_name)
    return _connection


