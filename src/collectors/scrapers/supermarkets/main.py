import sys
import os
import logging
import signal
from datetime import datetime

# Ensure the root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from collectors.scrapers.supermarkets.scraper import TescoScraper
from collectors.scrapers.supermarkets.config import TescoConfig
from database.mongo_connection import get_db_connection
from core.utils.validators.scraped_validator import validate_daily_bucket

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_daily_automatic_crawl():
    # 1. Initialize DB and Scraper
    db = get_db_connection()
    collection = db[TescoConfig.MONGO_COLLECTION]
    
    # Set headless=False so you can help with security blocks if needed
    scraper = TescoScraper(headless=False) 
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n🚀 Starting Automatic Food Crawl for: {today_str}")
    print(f"--- Targeting {len(TescoConfig.CATEGORY_URLS)} Categories ---")
    print(f"--- Standard Page Limit: {TescoConfig.MAX_PAGES_PER_CATEGORY} ---\n")

    for url in TescoConfig.CATEGORY_URLS:
        # Determine clean category name (e.g., 'bakery')
        category_slug = url.split('/')[-2] 
        
        logger.info(f"📂 Processing Category: {category_slug.upper()}")

        try:
            # 2. Scrape using our new standard limit from Config
            all_products = scraper.scrape_category_with_pagination(
                url=url, 
                category=category_slug,
                max_pages=TescoConfig.MAX_PAGES_PER_CATEGORY
            )

            if all_products:
                # 3. Construct the 'Bucket' Document
                daily_bucket = {
                    "_id": f"{today_str}_tesco_{category_slug}",
                    "date": datetime.now(),
                    "date_str": today_str,
                    "supermarket": "Tesco",
                    "category": category_slug,
                    "count": len(all_products),
                    "products": all_products 
                }

                # 4. Validate and Save
                try:
                    validate_daily_bucket(daily_bucket)
                    
                    # upsert=True replaces old data if you run it twice in one day
                    collection.replace_one(
                        {"_id": daily_bucket["_id"]}, 
                        daily_bucket, 
                        upsert=True
                    )
                    logger.info(f"✅ SAVED: {len(all_products)} items to bucket '{daily_bucket['_id']}'")
                
                except ValueError as e:
                    logger.error(f"❌ Validation failed for {category_slug}: {e}")

            else:
                logger.warning(f"⚠️ No products found for {category_slug}. Skipping database update.")

        except KeyboardInterrupt:
            print("\n🛑 Stop signal received (Ctrl+C). Closing browser and exiting...")
            break
        except Exception as e:
            logger.error(f"❌ Error during {category_slug} crawl: {e}")
            continue # Move to next category if one fails

    print(f"\n✨ Crawl completed for {today_str}")

if __name__ == "__main__":
    run_daily_automatic_crawl()