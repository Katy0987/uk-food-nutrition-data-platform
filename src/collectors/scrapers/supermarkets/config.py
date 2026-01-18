# collectors/scrapers/supermarkets/config.py

import os

class TescoConfig:
    # Base URL for Tesco Groceries
    BASE_URL = "https://www.tesco.com/groceries/en-GB"
    
    # Target Categories to scrape (URLs)
    # We use specific aisle URLs to ensure we get a good mix of products
    CATEGORY_URLS = [
        f"{BASE_URL}/shop/fresh-food/milk-butter-and-eggs/milk",
        f"{BASE_URL}/shop/bakery/bread-and-rolls/white-bread",
        f"{BASE_URL}/shop/fresh-food/fresh-fruit/bananas"
    ]

    # HTTP Headers to mimic a real browser (Ethical scraping requires identifying or mimicking standard traffic)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    # Throttling to be polite (Seconds)
    MIN_DELAY = 3
    MAX_DELAY = 7

    # MongoDB Configuration
    MONGO_DB_NAME = "food_price_db"
    MONGO_COLLECTION = "prices"