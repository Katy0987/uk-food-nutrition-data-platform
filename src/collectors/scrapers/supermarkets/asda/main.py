"""
Main script to run Asda supermarket category scraping
Stores results in MongoDB using daily bucket schema
"""

import sys
import os
import logging
from datetime import datetime
from src.collectors.scrapers.supermarkets.asda.scraper import AsdaScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'asda_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Category mapping
CATEGORY_MAP = {
    "Fruit": "https://www.asda.com/groceries/fruit-veg-flowers/fruit",
    "Vegetables": "https://www.asda.com/groceries/fruit-veg-flowers/vegetables-potatoes",
    "Meat": "https://www.asda.com/groceries/meat-poultry-fish/meat-poultry",
    "Fish": "https://www.asda.com/groceries/meat-poultry-fish/fish-seafood",
    "Bakery": "https://www.asda.com/groceries/bakery/bread-rolls",
    "Dessert": "https://www.asda.com/groceries/bakery/desserts-cream-cakes",
    "Protein": "https://www.asda.com/groceries/chilled-food/milk-butter-cream-eggs",
    "Cheese": "https://www.asda.com/groceries/chilled-food/cheese",
    "Sweets": "https://www.asda.com/groceries/food-cupboard/chocolates-sweets"
}

def get_db_connection():
    """Get MongoDB connection."""
    try:
        # Import here to avoid issues if MongoDB is not available
        from pymongo import MongoClient
        
        client = MongoClient("mongodb://localhost:27017/")
        # Test connection
        client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.error("   Make sure MongoDB is running on localhost:27017")
        raise

def run_supermarket_bucket_crawl(
    categories_to_scrape=None,
    max_products_per_category=50,
    headless=False
):
    """
    Run the scraping process for Asda supermarket.
    
    Args:
        categories_to_scrape: List of category names to scrape. If None, scrape all.
        max_products_per_category: Maximum number of products to scrape per category
        headless: Whether to run browser in headless mode
    """
    
    logger.info("=" * 80)
    logger.info("🚀 Starting Asda Supermarket Scraping")
    logger.info("=" * 80)
    
    # Initialize scraper
    scraper = AsdaScraper(headless=headless)
    
    # Connect to database
    try:
        db_client = get_db_connection()
        db = db_client["UK_food_intelligence_platform"]
        collection = db["Asda_products"]
    except Exception as e:
        logger.error(f"Cannot proceed without database connection")
        return
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Determine which categories to scrape
    if categories_to_scrape:
        categories = {k: v for k, v in CATEGORY_MAP.items() if k in categories_to_scrape}
    else:
        categories = CATEGORY_MAP
    
    logger.info(f"📋 Scraping {len(categories)} categories")
    logger.info(f"📅 Date: {date_str}")
    logger.info(f"🎯 Target: {max_products_per_category} products per category")
    logger.info("")
    
    # Statistics
    total_products = 0
    successful_categories = 0
    failed_categories = []
    
    # Scrape each category
    for idx, (cat_name, url) in enumerate(categories.items(), 1):
        logger.info("─" * 80)
        logger.info(f"📦 [{idx}/{len(categories)}] Category: {cat_name}")
        logger.info("─" * 80)
        
        try:
            # Scrape the category
            product_list = scraper.scrape_category_bucket(
                cat_name, 
                url, 
                max_products=max_products_per_category
            )
            
            if product_list:
                # Create bucket document
                bucket_id = f"{cat_name.replace(' ', '_')}_{date_str}"
                bucket_doc = {
                    "_id": bucket_id,
                    "store": "Asda",
                    "category": cat_name,
                    "date": date_str,
                    "item_count": len(product_list),
                    "products": product_list,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "url": url
                }
                
                # Save to MongoDB
                result = collection.update_one(
                    {"_id": bucket_id}, 
                    {"$set": bucket_doc}, 
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    logger.info(f"💾 ✅ Bucket Saved: {bucket_id}")
                    logger.info(f"   📊 Products: {len(product_list)}")
                    
                    # Count products with nutrition
                    with_nutrition = sum(1 for p in product_list if p.get('nutrition'))
                    if with_nutrition > 0:
                        logger.info(f"   📈 Nutrition data: {with_nutrition}/{len(product_list)} products")
                    
                    total_products += len(product_list)
                    successful_categories += 1
                else:
                    logger.warning(f"⚠️  Database update failed for {bucket_id}")
            else:
                logger.warning(f"⚠️  No products scraped for {cat_name}")
                failed_categories.append(cat_name)
                
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
            logger.info("💾 Saving progress...")
            break
            
        except Exception as e:
            logger.error(f"❌ Error in category {cat_name}: {str(e)}")
            failed_categories.append(cat_name)
            
            # Log full traceback
            import traceback
            logger.error(traceback.format_exc())
            
            # Continue with next category
            continue
        
        logger.info("")
    
    # Print summary
    logger.info("=" * 80)
    logger.info("📊 SCRAPING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Successful categories: {successful_categories}/{len(categories)}")
    logger.info(f"📦 Total products scraped: {total_products}")
    
    if failed_categories:
        logger.info(f"❌ Failed categories: {', '.join(failed_categories)}")
    
    logger.info(f"💾 Database: UK_food_intelligence_platform.Asda_products")
    logger.info("=" * 80)
    
    # Close database connection
    db_client.close()
    logger.info("🔒 Database connection closed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Asda supermarket products')
    parser.add_argument(
        '--categories',
        nargs='+',
        help='Specific categories to scrape (default: all)',
        choices=list(CATEGORY_MAP.keys())
    )
    parser.add_argument(
        '--max-products',
        type=int,
        default=50,
        help='Maximum products per category (default: 50)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    try:
        run_supermarket_bucket_crawl(
            categories_to_scrape=args.categories,
            max_products_per_category=args.max_products,
            headless=args.headless
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)