import requests
import json
import time
import random
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

# Import Config and Model
from collectors.scrapers.supermarkets.config import TescoConfig
from core.models.price import FoodPrice  # Ensure this matches your model file

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TescoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(TescoConfig.HEADERS)
        self.search_url = "https://www.tesco.com/groceries/en-GB/search?query="

    def _sleep(self):
        """Ethical delay between requests to avoid being blocked."""
        delay = random.uniform(TescoConfig.MIN_DELAY, TescoConfig.MAX_DELAY)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML with error handling and ethical delays."""
        try:
            self._sleep()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _clean_price(self, price_str: str) -> float:
        """Helper to convert price string (e.g. '£1.50') to float (1.50)."""
        try:
            clean = price_str.replace('£', '').replace('GBP', '').strip()
            return float(clean)
        except ValueError:
            return 0.0

    # --- NEW METHOD FOR OPTION 1 (DATABASE SYNC) ---
    def search_and_extract(self, product_name: str) -> Optional[Dict]:
        """
        Searches for a specific product name and returns the top result.
        Perfect for updating existing MongoDB Compass documents.
        """
        formatted_query = product_name.replace(" ", "+")
        url = f"{self.search_url}{formatted_query}"
        
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for the first product item in search results
        # Tesco usually uses a list item or a specific div for the tile
        product_card = soup.find("li", class_=lambda x: x and "product-list--list-item" in x)
        
        if product_card:
            return self.parse_product_card(product_card)
        return None

    # --- UPDATED PARSING LOGIC ---
    def parse_product_card(self, card_soup) -> Optional[Dict]:
        """Extracts data from an individual HTML product card."""
        try:
            # 1. Name
            name_tag = card_soup.find("a", {"class": lambda x: x and "product-tile" in x and "title" in x})
            if not name_tag:
                name_tag = card_soup.find("h3")
            product_name = name_tag.get_text(strip=True) if name_tag else "Unknown"

            # 2. Price
            price_tag = card_soup.find("p", {"class": lambda x: x and "price-text" in x})
            if not price_tag:
                 price_tag = card_soup.find("span", string=lambda text: text and "£" in text)
            
            raw_price = price_tag.get_text(strip=True) if price_tag else "0.00"
            price_float = self._clean_price(raw_price)

            # 3. URL
            link_tag = card_soup.find('a', href=True)
            full_url = "https://www.tesco.com" + link_tag['href'] if link_tag else None

            return {
                "supermarket": "Tesco",
                "name": product_name, # Matches your 'name' field in Compass
                "category": "Dairy",
                "price": {
                    "value": price_float,
                    "unit": "GBP"
                },
                "scraped_at": datetime.now() # MongoDB likes Python datetime objects
            }
        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            return None

    # --- CATEGORY SCRAPING (ORIGINAL STRATEGY) ---
    def extract_products_from_json_ld(self, html: str, category_context: str) -> List[Dict]:
        """Robust extraction via Schema.org JSON-LD."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        item_data = item.get('item', {})
                        if item_data:
                            products.append({
                                "source": "tesco",
                                "product_name": item_data.get('name'),
                                "category": category_context,
                                "price": float(item_data.get('offers', {}).get('price', 0.0)),
                                "unit": item_data.get('offers', {}).get('priceCurrency', 'GBP'),
                                "timestamp": datetime.now().strftime("%Y-%m-%d")
                            })
            except:
                continue
        return products