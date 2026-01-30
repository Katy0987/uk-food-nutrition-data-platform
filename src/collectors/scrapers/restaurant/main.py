# main.py
from datetime import datetime
from src.collectors.scrapers.restaurant.scraper import McDonaldsScraper
from src.database.mongo_connection import get_db_connection
from datetime import datetime
from bson import Int64

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
    scraper = McDonaldsScraper(headless=False)
    db = get_db_connection()["UK_food_intelligence_platform"]
    collection = db["McDonalds_products"]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    print("🚀 Starting Optimized McDonald's Scrape...")

    for category, url in CATEGORY_MAP.items():

        # -------- STEP 2: scrape + collect ----------
        products = scraper.scrape_category_complete(category, url)

        if not products:
            print(f"⚠️ No products scraped for {category}")
            continue

        doc_id = f"{category}_{today}"

        bucket_document = {
            "_id": doc_id,
            "metadata": {
                "date": today,
                "timestamp": timestamp,   # string = safe
                "supermarket": "McDonalds",
                "category": category
            },
            "products": products
        }

        # -------- STEP 3: sanitize BEFORE Mongo ----------
        safe_bucket_document = mongo_safe(bucket_document)

        collection.replace_one(
            {"_id": doc_id},
            safe_bucket_document,
            upsert=True
        )

        print(f"📦 Saved bucket: {doc_id} ({len(products)} items)")

    print("\n✨ Mission Accomplished!")

if __name__ == "__main__":
    run_mcdonalds_automated_crawl()
