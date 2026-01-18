import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to hold the single instance of the client
_mongo_client = None

def get_mongo_client():
    """
    Returns a singleton MongoClient instance.
    Initializes the connection if it doesn't exist.
    """
    global _mongo_client
    
    if _mongo_client is None:
        # 1. Configuration
        # Load from Environment Variables (Best Practice) or use default local
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        MAX_POOL_SIZE = int(os.getenv("MONGO_POOL_SIZE", 100))
        
        try:
            logger.info(f"Connecting to MongoDB at {MONGO_URI}...")
            
            # 2. Initialize Client
            # serverSelectionTimeoutMS=5000 ensures we fail fast (5s) if Mongo is down
            client = MongoClient(
                MONGO_URI,
                maxPoolSize=MAX_POOL_SIZE,
                serverSelectionTimeoutMS=5000
            )
            
            # 3. Verify Connection ('Ping' the server)
            # This triggers the actual network connection
            client.admin.command('ping')
            
            logger.info("✅ Successfully connected to MongoDB.")
            _mongo_client = client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.critical(f"❌ Failed to connect to MongoDB: {e}")
            raise e
            
    return _mongo_client

def get_db_connection(db_name="food_price_db"):
    """
    Helper function to get a specific database object directly.
    """
    client = get_mongo_client()
    return client[db_name]

def close_mongo_connection():
    """
    Closes the MongoDB connection. 
    Call this when the application shuts down.
    """
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed.")
        _mongo_client = None