import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_URL)
    
    # Retry logic: Try to connect 5 times with a 5-second delay
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            # Simple command to check connection
            await db.client.admin.command('ping')
            
            # If successful, create indices
            await db.client[settings.DB_NAME]["active_rides"].create_index([("location", "2dsphere")])
            logger.info("✅ Successfully connected to MongoDB!")
            return
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                logger.info("⏳ Waiting 5 seconds before retrying...")
                await asyncio.sleep(5)
            else:
                logger.error("❌ Could not connect to MongoDB after multiple attempts.")
                raise e

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db.client[settings.DB_NAME]