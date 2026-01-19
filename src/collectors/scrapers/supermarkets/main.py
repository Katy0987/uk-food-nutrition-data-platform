import sys
import os
import logging
from datetime import datetime

# Ensure the root directory is in python path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from collectors.scrapers.supermarkets.scraper import TescoScraper
from collectors.scrapers.supermarkets.config import TescoConfig
from database.mongo_connection import get_db_connection
from core.utils.validators.scraped_validator import validate_daily_bucket
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_daily_automatic_crawl():
    """
    The main execution logic:
    1. Connects to MongoDB.
    2. Loops through food categories.
    3. Scrapes all products (with pagination).
    4. Saves them as a single 'Daily Bucket' document.
    """
    try:
        db = get_db_connection()
        # Uses the collection name from your config (e.g., 'daily_scrapes')
        collection = db[TescoConfig.MONGO_COLLECTION]
        scraper = TescoScraper()

        # Generate a standard timestamp for today
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🚀 Starting Automatic Food Crawl for: {today_str}")
        print(f"--- Targeting {len(TescoConfig.CATEGORY_URLS)} Categories ---")

        for url in TescoConfig.CATEGORY_URLS:
            # 1. Determine a clean category name from the URL
            # e.g., 'fresh-food' from '.../fresh-food/all'
            category_slug = url.split('/')[-2] 
            
            logger.info(f"📂 Processing Category: {category_slug.upper()}")

            # 2. Scrape all items across multiple pages (Automatically handles pagination)
            all_products = scraper.scrape_category_with_pagination(url, category_slug)

            if all_products:
                # 3. Construct the 'Bucket' Document
                # The _id is unique per day/category to prevent duplicate documents
                daily_bucket = {
                    "_id": f"{today_str}_tesco_{category_slug}",
                    "date": datetime.now(), # Stored as a Date object for Compass filtering
                    "date_str": today_str,
                    "supermarket": "Tesco",
                    "category": category_slug,
                    "count": len(all_products),
                    "products": all_products  # This is the big array of all food items
                }

                # Run the validator
                try:
                    validate_daily_bucket(daily_bucket)
                    collection.replace_one({"_id": daily_bucket["_id"]}, daily_bucket, upsert=True)
                except ValueError as e:
                    logger.error(f"❌ Validation failed: {e}")

                # 4. Save to MongoDB
                # replace_one + upsert=True means: 
                # If the doc exists (you ran it twice today), overwrite it.
                # If it doesn't exist, create it.
                collection.replace_one(
                    {"_id": daily_bucket["_id"]},
                    daily_bucket,
                    upsert=True
                )
                print(f"Created new bucket in supermarket.price: {daily_bucket['_id']}")
                logger.info(f"✅ SUCCESSFULLY SAVED: {len(all_products)} products to bucket '{daily_bucket['_id']}'")
            else:
                logger.warning(f"⚠️ No products were found for {category_slug}. Check if Tesco changed their layout.")

    except Exception as e:
        logger.error(f"❌ Critical error during the crawl: {e}")

if __name__ == "__main__":
    run_daily_automatic_crawl()