# main.py
import logging
import sys
from datetime import datetime
from src.collectors.scrapers.restaurant.scraper import McDonaldsScraper
from src.database.mongo_connection import get_db_connection
from bson import Int64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mcdonalds_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

INT64_MAX = 2**63 - 1
INT64_MIN = -2**63

def mongo_safe(value):
    """
    Recursively convert Python objects to Mongo-safe types.
    """
    if isinstance(value, int):
        if value > INT64_MAX or value < INT64_MIN:
            return str(value)
        return Int64(value)

    elif isinstance(value, float):
        return value

    elif isinstance(value, dict):
        return {k: mongo_safe(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [mongo_safe(v) for v in value]

    elif isinstance(value, datetime):
        return value

    else:
        return value


CATEGORY_MAP = {
    "Breakfast": "https://www.mcdonalds.com/gb/en-gb/menu/breakfast.html",
    "Fries & Sides": "https://www.mcdonalds.com/gb/en-gb/menu/fries-and-sides.html",
    "Desserts": "https://www.mcdonalds.com/gb/en-gb/menu/desserts.html",
    "Burgers": "https://www.mcdonalds.com/gb/en-gb/menu/burgers.html",
    "Vegan": "https://www.mcdonalds.com/gb/en-gb/menu/vegan.html",
    "Drinks": "https://www.mcdonalds.com/gb/en-gb/menu/milkshakes-and-cold-drinks.html",
    "Chicken & Nuggets": "https://www.mcdonalds.com/gb/en-gb/menu/chicken-mcnuggets-and-selects.html",
    "Wraps & Salads": "https://www.mcdonalds.com/gb/en-gb/menu/wraps-and-salads.html"
}

def run_mcdonalds_automated_crawl():
    """
    Main scraping function with improved error handling and progress tracking.
    """
    logger.info("=" * 80)
    logger.info("🚀 Starting McDonald's Menu Scraper")
    logger.info("=" * 80)
    
    scraper = McDonaldsScraper(headless=False)
    db = get_db_connection()["UK_food_intelligence_platform"]
    collection = db["McDonalds_products"]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info(f"📅 Date: {today}")
    logger.info(f"📂 Categories to scrape: {len(CATEGORY_MAP)}")
    logger.info("")
    
    # Track statistics
    total_products = 0
    successful_categories = 0
    failed_categories = []

    for idx, (category, url) in enumerate(CATEGORY_MAP.items(), 1):
        logger.info("─" * 80)
        logger.info(f"📦 [{idx}/{len(CATEGORY_MAP)}] Category: {category}")
        logger.info("─" * 80)
        
        try:
            # Scrape category with improved retry logic
            products = scraper.scrape_category_complete(category, url)

            if not products:
                logger.warning(f"⚠️  No products scraped for {category}")
                failed_categories.append(category)
                continue

            # Create bucket document
            doc_id = f"{category.replace(' & ', '_').replace(' ', '_')}_{today}"

            bucket_document = {
                "_id": doc_id,
                "metadata": {
                    "date": today,
                    "timestamp": timestamp,
                    "supermarket": "McDonalds",
                    "category": category
                },
                "products": products,
                "item_count": len(products)
            }

            # Sanitize for MongoDB
            safe_bucket_document = mongo_safe(bucket_document)

            # Save to database
            result = collection.replace_one(
                {"_id": doc_id},
                safe_bucket_document,
                upsert=True
            )

            logger.info(f"💾 ✅ Bucket Saved: {doc_id}")
            logger.info(f"   📊 Products: {len(products)}")
            
            total_products += len(products)
            successful_categories += 1

        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
            logger.info("💾 Saving progress...")
            break
        
        except Exception as e:
            logger.error(f"❌ Error in category {category}: {str(e)}")
            failed_categories.append(category)
            
            import traceback
            logger.error(traceback.format_exc())
            
            continue
        
        logger.info("")

    # Print final summary
    logger.info("=" * 80)
    logger.info("📊 SCRAPING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Successful categories: {successful_categories}/{len(CATEGORY_MAP)}")
    logger.info(f"📦 Total products scraped: {total_products}")
    
    if failed_categories:
        logger.info(f"❌ Failed categories: {', '.join(failed_categories)}")
    
    logger.info(f"💾 Database: UK_food_intelligence_platform.McDonalds_products")
    logger.info("=" * 80)
    logger.info("\n✨ Mission Accomplished!")

if __name__ == "__main__":
    try:
        run_mcdonalds_automated_crawl()
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
