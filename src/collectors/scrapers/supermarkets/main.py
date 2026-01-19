import sys
import os
import logging
from datetime import datetime

# Ensure the root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from collectors.scrapers.supermarkets.scraper import TescoScraper
from collectors.scrapers.supermarkets.config import TescoConfig
from database.mongo_connection import get_db_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_existing_items(db, scraper):

    collection = db["price"] 
    
    existing_docs = list(collection.find({}, {"name": 1, "_id": 1}))
    
    if not existing_docs:
        logger.info("No existing documents found in Compass to sync.")
        return

    logger.info(f"🔄 Found {len(existing_docs)} items in Compass. Starting sync...")
    
    for doc in existing_docs:
        product_name = doc.get("name") # Getting the 'name' field
        if not product_name:
            continue

        logger.info(f"🔍 Searching Tesco for: {product_name}")
        
        # Scraper returns a dict. Let's extract the new price.
        latest_info = scraper.search_and_extract(product_name)
        
        if latest_info:
            # 3. Use Dot Notation to update ONLY the nested value
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "price.value": latest_info["price"], # Updates the nested value
                    "scraped_at": datetime.utcnow()      # Sets as a proper Mongo Date object
                }}
            )
            logger.info(f"✅ Updated {product_name} to £{latest_info['price']}")
        else:
            logger.warning(f"⚠️ Could not find search result for {product_name}")

def discover_new_items(db, scraper, limit=50):
    """
    Original logic: Scrapes categories to find NEW products.
    """
    collection = db[TescoConfig.MONGO_COLLECTION]
    all_products = []
    
    logger.info("🌐 Starting Discovery: Scraping categories for new items...")
    
    for url in TescoConfig.CATEGORY_URLS:
        if len(all_products) >= limit:
            break
            
        category_name = url.split('/')[-1].replace('-', ' ').capitalize()
        products = scraper.scrape_category(url, category_name)
        all_products.extend(products)

    if all_products:
        # We use 'upsert' logic even for new items to prevent duplicates
        for prod in all_products[:limit]:
            collection.update_one(
                {"product_name": prod["product_name"]},
                {"$set": prod},
                upsert=True
            )
        logger.info(f"✨ Discovery complete. Processed {len(all_products[:limit])} items.")

def main():
    try:
        db = get_db_connection()
        scraper = TescoScraper()

        print("--- Tesco Price Manager ---")
        print("1. Sync/Update existing items (Compass List)")
        print("2. Discover new items (Category Scraping)")
        print("3. Run both")
        
        # You can automate this choice or hardcode it
        choice = "3" 

        if choice in ["1", "3"]:
            sync_existing_items(db, scraper)
        
        if choice in ["2", "3"]:
            discover_new_items(db, scraper, limit=50)

    except Exception as e:
        logger.error(f"❌ Critical error in main execution: {e}")

if __name__ == "__main__":
    main()