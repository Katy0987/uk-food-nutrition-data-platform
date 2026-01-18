import sys
import os

# Ensure the root directory is in the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from collectors.scrapers.restaurant.scraper import McDonaldsScraper
from database.mongo_connection import get_db_connection

def run_mcdonalds_scraper():
    scraper = McDonaldsScraper()
    db = get_db_connection()
    collection = db["restaurant_prices"]

    print("🚀 Starting McDonald's UK Scraper...")
    
    # 1. Get the links for 20 products
    product_links = scraper.get_product_links(limit=20)
    
    scraped_count = 0
    for link in product_links:
        try:
            print(f"📄 Scraping: {link}")
            product_model = scraper.scrape_product_details(link)
            
            if product_model:
                # 2. Convert to dict for MongoDB
                document = product_model.to_dict()
                
                # 3. Upsert (Update if exists by URL, else Insert)
                collection.update_one(
                    {"url": document["url"]},
                    {"$set": document},
                    upsert=True
                )
                scraped_count += 1
                print(f"✅ Saved: {document['product_name']}")
            
        except Exception as e:
            print(f"❌ Error scraping {link}: {e}")

    print(f"\n✨ Scraping Complete! Successfully processed {scraped_count} items.")

if __name__ == "__main__":
    run_mcdonalds_scraper()