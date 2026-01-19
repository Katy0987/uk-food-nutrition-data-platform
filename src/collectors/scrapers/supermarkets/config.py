import os

class TescoConfig:
    # Base URL for Tesco Groceries
    BASE_URL = "https://www.tesco.com/groceries/en-GB"
    
    # 1. UPDATED: Using "All" category links to catch EVERY food product automatically
    CATEGORY_URLS = [
        f"{BASE_URL}/shop/fresh-food/all",
        f"{BASE_URL}/shop/bakery/all",
        f"{BASE_URL}/shop/frozen-food/all",
        f"{BASE_URL}/shop/food-cupboard/all",
        f"{BASE_URL}/shop/drinks/all"
        f"{BASE_URL}/shop/treats-and-snacks/all"
    ]

    # 2. NEW: Pagination Control
    # Increase this if you want more data, decrease for faster testing
    MAX_PAGES_PER_CATEGORY = 5 

    # HTTP Headers (Keep these to mimic a real browser)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    # Throttling (Keep these to stay ethical and avoid blocks)
    MIN_DELAY = 2
    MAX_DELAY = 5

    # 3. UPDATED: Database Configuration
    # Using the new "bucket" collection name for clarity
    MONGO_DB_NAME = "UK_food_intelligence_platform"
    MONGO_COLLECTION = "supermarket.price"