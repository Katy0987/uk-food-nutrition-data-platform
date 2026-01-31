"""
Fixed Sainsbury's Main Script with Validation
"""
from datetime import datetime
from src.collectors.scrapers.supermarkets.sainsbury.scraper import SainsburysScraper
from src.database.mongo_connection import get_db_connection
import logging
from src.core.utils.validators.scraped_validator import validate_daily_bucket, ValidationError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "Fruit and Vegetable": "https://www.sainsburys.co.uk/gol-ui/groceries/fruit-and-vegetables/c:1020082",
    "Meat and Fish": "https://www.sainsburys.co.uk/gol-ui/groceries/meat-and-fish/c:1020388",
    "Chilled Food": "https://www.sainsburys.co.uk/gol-ui/groceries/chilled-food/c:1019184",
    "Bakery": "https://www.sainsburys.co.uk/gol-ui/groceries/bakery/c:1018859",
    "Food Cupboard": "https://www.sainsburys.co.uk/gol-ui/groceries/food-cupboard/c:1019883",
    "Drinks": "https://www.sainsburys.co.uk/gol-ui/groceries/drinks/c:1019463"
}

def run_supermarket_bucket_crawl():
    """Main function to scrape all categories."""
    
    print("\n" + "="*70)
    print("🛒 SAINSBURY'S SCRAPER - FIXED VERSION")
    print("="*70 + "\n")
    
    # Initialize scraper (headless=False so you can see what's happening)
    scraper = SainsburysScraper(headless=False)
    
    # Connect to database
    db_client = get_db_connection()
    db = db_client["UK_food_intelligence_platform"]
    collection = db["Sainsbury_products"]

    date_str = datetime.now().strftime("%Y-%m-%d")
    
    successful = 0
    failed = 0

    for cat_name, url in CATEGORY_MAP.items():
        print(f"\n{'='*70}")
        print(f"📂 Category: {cat_name}")
        print(f"{'='*70}")
        
        try:
            # Scrape category (max 50 products)
            products = scraper.scrape_category_bucket(cat_name, url, max_products=50)

            if not products:
                print(f"⚠️  No products found for {cat_name}")
                failed += 1
                continue

            # Create bucket document
            bucket_id = f"{cat_name.replace(' ', '_')}_{date_str}"
            
            bucket_doc = {
                "_id": bucket_id,
                "store": "Sainsbury",
                "category": cat_name,
                "date": date_str,
                "item_count": len(products),
                "products": products,
                "created_at": datetime.utcnow().isoformat()
            }

            # ✅ VALIDATE BEFORE SAVING - ADD THIS BLOCK
            try:
                validate_daily_bucket(bucket_doc)
                logger.info(f"✅ Validation passed for {bucket_id}")
            except ValidationError as e:
                logger.error(f"❌ Validation failed for {cat_name}: {e}")
                print(f"❌ Validation failed: {e}")
                failed += 1
                continue  # Skip saving this category
            # END OF VALIDATION BLOCK

            # Save to database (only if validation passed)
            collection.update_one(
                {"_id": bucket_id},
                {"$set": bucket_doc},
                upsert=True
            )

            print(f"✅ Saved {bucket_id} ({len(products)} products)")
            successful += 1

        except Exception as e:
            print(f"❌ Error in category {cat_name}: {e}")
            logger.error(f"Error details: {e}", exc_info=True)
            failed += 1
            continue
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SCRAPING SUMMARY")
    print("="*70)
    print(f"✅ Successful categories: {successful}")
    print(f"❌ Failed categories: {failed}")
    print(f"📅 Date: {date_str}")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_supermarket_bucket_crawl()