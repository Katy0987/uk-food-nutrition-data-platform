import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from core.models.food import FoodItem

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class McDonaldsScraper:
    def __init__(self):
        self.base_url = "https://www.mcdonalds.com"
        self.menu_url = f"{self.base_url}/gb/en-gb/menu.html"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9"
        }

    def get_product_links(self, limit=20):
        """Fetches product URLs from the main menu page."""
        logger.info("Fetching menu categories...")
        response = requests.get(self.menu_url, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch menu: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        # McDonald's UK uses 'item-link' or similar for product tiles
        links = []
        for a in soup.find_all("a", href=True):
            if "/product/" in a['href'] and a['href'] not in links:
                links.append(self.base_url + a['href'] if a['href'].startswith("/") else a['href'])
                if len(links) >= limit:
                    break
        
        logger.info(f"Found {len(links)} product links.")
        return links

    def scrape_product_details(self, url):
        """Scrapes detailed info from an individual product page."""
        time.sleep(random.uniform(1, 3)) # Ethical delay
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extraction Logic (Selectors based on McDonald's UK structure)
        name = soup.find("h1", class_="product-title")
        desc = soup.find("div", class_="product-description")
        
        # Calories are often in a specific span/div
        calories_tag = soup.find(string=lambda t: "kcal" in t.lower())
        calories = None
        if calories_tag:
            try:
                # Extracts '493' from '493 kcal'
                calories = int(''.join(filter(str.isdigit, calories_tag)))
            except:
                pass

        # Since McDonald's UK prices vary by location, we use a 'Starting From' 
        # placeholder or mock if not available on the global product page
        # In a real scenario, you'd pass a store ID cookie.
        mock_price = round(random.uniform(1.29, 6.99), 2) 

        item_data = {
            "url": url,
            "product_name": name.text.strip() if name else "Unknown Product",
            "description": desc.text.strip() if desc else "",
            "category": "Main Menu", # Simplified for now
            "price": mock_price,
            "calories": calories,
            "source": "mcdonalds",
            "is_vegetarian": "vegetarian" in (desc.text.lower() if desc else ""),
            "tags": ["Scraped", "Restaurant"]
        }
        
        return FoodItem.from_scraped_item(item_data)