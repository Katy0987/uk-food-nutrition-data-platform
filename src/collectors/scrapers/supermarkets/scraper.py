import requests
import json
import time
import random
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

# Import Config
from collectors.scrapers.supermarkets.config import TescoConfig

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TescoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(TescoConfig.HEADERS)
        self.products_scraped = []

    def _sleep(self):
        """Ethical delay between requests."""
        delay = random.uniform(TescoConfig.MIN_DELAY, TescoConfig.MAX_DELAY)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetches the HTML content of a page with error handling."""
        try:
            self._sleep()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def parse_product_card(self, card_soup) -> Optional[Dict]:
        """
        Extracts product details from a single HTML product card.
        Tries to find specific data attributes or classes.
        """
        try:
            # 1. Extract Name
            # Tesco uses various classes, looking for links inside the tile is reliable
            name_tag = card_soup.find("a", {"class": lambda x: x and "product-tile" in x and "title" in x})
            if not name_tag:
                # Fallback generic check
                name_tag = card_soup.find("h3")
            
            product_name = name_tag.get_text(strip=True) if name_tag else "Unknown Product"

            # 2. Extract Price
            # Look for the specific price class usually containing the currency symbol
            price_tag = card_soup.find("p", {"class": lambda x: x and "price-text" in x})
            if not price_tag:
                 price_tag = card_soup.find("span", string=lambda text: text and "£" in text)
            
            raw_price = price_tag.get_text(strip=True) if price_tag else "0.00"
            # Clean price string (remove '£' and handled 'p')
            price_float = self._clean_price(raw_price)

            # 3. Category (passed in context usually, but we can guess or leave generic)
            category = "Groceries" 

            return {
                "source": "tesco",
                "product_name": product_name,
                "category": category,
                "price": price_float,
                "unit": "GBP",
                "timestamp": datetime.now().strftime("%Y-%m-%d")
            }
        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            return None

    def _clean_price(self, price_str: str) -> float:
        """Helper to convert price string to float."""
        try:
            clean = price_str.replace('£', '').replace('GBP', '').strip()
            return float(clean)
        except ValueError:
            return 0.0

    def extract_products_from_json_ld(self, html: str, category_context: str) -> List[Dict]:
        """
        Primary Extraction Method: Looks for structured data (JSON-LD) 
        which is more robust than CSS scraping.
        """
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Tesco often embeds product data in script tags with type application/ld+json
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                # JSON-LD can be a list or a dict. We look for 'Product' or 'ItemList'
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        item_data = item.get('item', {})
                        if item_data:
                            # Map to our price_document model
                            price_doc = {
                                "source": "tesco",
                                "product_name": item_data.get('name'),
                                "category": category_context,
                                "price": float(item_data.get('offers', {}).get('price', 0.0)),
                                "unit": item_data.get('offers', {}).get('priceCurrency', 'GBP'),
                                "timestamp": datetime.now().strftime("%Y-%m-%d")
                            }
                            products.append(price_doc)
            except (json.JSONDecodeError, AttributeError, ValueError):
                continue
        
        return products

    def scrape_category(self, url: str, category_name: str) -> List[Dict]:
        """Main method to process a category URL."""
        html = self.fetch_page(url)
        if not html:
            return []

        # Strategy 1: Try JSON-LD (Best for correctness)
        extracted = self.extract_products_from_json_ld(html, category_name)
        
        # Strategy 2: Fallback to HTML parsing if JSON-LD is empty
        if not extracted:
            logger.info("JSON-LD not found, switching to HTML parsing...")
            soup = BeautifulSoup(html, 'html.parser')
            # Tesco generic product list wrapper
            product_cards = soup.find_all("li", class_=lambda x: x and "product-list--list-item" in x)
            
            for card in product_cards:
                data = self.parse_product_card(card)
                if data and data['price'] > 0:
                    data['category'] = category_name # Update category
                    extracted.append(data)

        logger.info(f"Found {len(extracted)} items in {category_name}")
        return extracted