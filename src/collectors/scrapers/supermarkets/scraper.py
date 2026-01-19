import requests
import json
import time
import random
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

# Import Updated Config
from collectors.scrapers.supermarkets.config import TescoConfig

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TescoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(TescoConfig.HEADERS)

    def _sleep(self):
        """Ethical delay between requests to avoid being blocked."""
        delay = random.uniform(TescoConfig.MIN_DELAY, TescoConfig.MAX_DELAY)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML with error handling and ethical delays."""
        try:
            self._sleep()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error on {url}. Server is too slow.")
            return None
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

    # --- NEW PAGINATION LOGIC ---
    def scrape_category_with_pagination(self, base_url: str, category_name: str) -> List[Dict]:
        """
        Automatically turns pages to collect all food products in a category.
        """
        all_products = []
        page_number = 1
        
        # 
        while page_number <= TescoConfig.MAX_PAGES_PER_CATEGORY:
            # Construct the URL for the current page
            paginated_url = f"{base_url}?page={page_number}"
            logger.info(f"📄 Scraping {category_name} - Page {page_number}")
            
            html = self.fetch_page(paginated_url)
            if not html:
                break
            
            # Extract products from this specific page
            page_items = self.extract_from_html(html)
            
            if not page_items:
                logger.info(f"⏹️ No more products found at page {page_number}. Ending category.")
                break
                
            all_products.extend(page_items)
            page_number += 1
            
        return all_products

    def extract_from_html(self, html: str) -> List[Dict]:
        """Finds all product cards on a page and parses them."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Tesco list items for products
        cards = soup.find_all("li", class_=lambda x: x and "product-list--list-item" in x)
        
        for card in cards:
            data = self.parse_product_card(card)
            if data:
                products.append(data)
        return products

    def parse_product_card(self, card_soup) -> Optional[Dict]:
        """Extracts simple info for the 'Bucket' array."""
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

            # Returning a simplified version for the Bucket Model
            return {
                "name": product_name,
                "price": price_float,
                "url": full_url
            }
        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            return None