# collectors/scrapers/supermarkets/main.py

import sys
import os

# Ensure the root directory is in python path to import core and database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from collectors.scrapers.supermarkets.scraper import TescoScraper
from collectors.scrapers.supermarkets.config import TescoConfig
from database.mongo_connection import get_db_connection
# Mocking the mongo connection import based on your prompt structure
# from database.mongo_connection import get_db_connection (Assuming this exists)
# For this code block to work standalone, I will stub the connection below.

def save_to_mongo(data_list):
    if not data_list:
        return

    try:
        # Get the database (default is "food_price_db")
        db = get_db_connection()

        # Select the collection defined in your config
        collection = db[TescoConfig.MONGO_COLLECTION]

        # Insert the data
        result = collection.insert_many(data_list)

        print(f"✅ Successfully inserted {len(result.inserted_ids)} documents into MongoDB.")

    except Exception as e:
        print(f"❌ Error saving to MongoDB: {e}")

def main():
    scraper = TescoScraper()
    all_products = []
    
    print("Starting Tesco Web Scraper...")
    
    # 1. Iterate through categories defined in Config
    for url in TescoConfig.CATEGORY_URLS:
        if len(all_products) >= 50:
            break
            
        # Extract category name from URL for metadata (e.g., 'milk' from '.../milk')
        category_name = url.split('/')[-1].replace('-', ' ').capitalize()
        
        print(f"Scraping category: {category_name}...")
        products = scraper.scrape_category(url, category_name)
        
        all_products.extend(products)

    # 2. Enforce limits (Focus on correctness/quality, limit to 50 as requested)
    final_dataset = all_products[:50]

    # 3. Store Data
    if final_dataset:
        save_to_mongo(final_dataset)
    else:
        print("Failed to collect data. Tesco may be blocking requests or layout changed.")

if __name__ == "__main__":
    main()