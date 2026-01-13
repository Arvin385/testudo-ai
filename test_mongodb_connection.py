"""
Test script to verify MongoDB connection.
"""

import os
from database import MongoDBConnection

def test_connection():
    """Test MongoDB connection."""
    # Use the provided URI or environment variable
    uri = os.getenv("MONGODB_URI", "mongodb+srv://testudoAIteam:fepgg9v5rA9ptcId@userdata.7nyu4ck.mongodb.net/?appName=UserData")
    
    print("Testing MongoDB connection...")
    print(f"URI: {uri[:50]}...")  # Print first 50 chars for security
    
    try:
        conn = MongoDBConnection(uri=uri, db_name="testudo_ai")
        db = conn.connect()
        
        # Test by listing collections
        collections = db.list_collection_names()
        print(f"✓ Successfully connected to MongoDB!")
        print(f"✓ Database: {db.name}")
        print(f"✓ Collections: {collections}")
        
        conn.disconnect()
        print("✓ Connection test completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()


