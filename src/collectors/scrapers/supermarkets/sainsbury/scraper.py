"""
Fixed Sainsbury's Scraper - Actually Works!
Handles the real Sainsbury's website structure.
"""

import logging
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class SainsburysScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless

    def _accept_cookies(self, page):
        """Improved cookie acceptance."""
        try:
            # Wait for and click the accept button
            page.wait_for_selector("#onetrust-accept-btn-handler", timeout=10000)
            page.click("#onetrust-accept-btn-handler")
            time.sleep(2)
            logger.info("🍪 Cookies accepted")
        except Exception as e:
            logger.info("🍪 No cookie banner or already accepted")

    def _wait_for_products(self, page):
        """Wait for products to load with multiple fallback strategies."""
        selectors_to_try = [
            'article[data-testid="product-tile"]',
            'div.pt__card',
            'article.pt',
            'div[class*="product"]',
            'a[href*="/product/"]'
        ]
        
        for selector in selectors_to_try:
            try:
                page.wait_for_selector(selector, timeout=10000)
                logger.info(f"✅ Products loaded (selector: {selector})")
                return True
            except:
                continue
        
        logger.warning("⚠️ Could not find products with standard selectors")
        return False

    def _scrape_product_detail(self, page, product_url):
        """Scrape individual product page."""
        try:
            page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for main content
            try:
                page.wait_for_selector("h1, .pd__header", timeout=10000)
            except:
                logger.warning(f"⚠️ Slow loading: {product_url}")
            
            time.sleep(random.uniform(1, 2))  # Be polite
            
            soup = BeautifulSoup(page.content(), "html.parser")

            # Name - try multiple selectors
            name = None
            name_selectors = ["h1", ".pd__header h1", "[data-testid='pd-product-name']"]
            for selector in name_selectors:
                name_tag = soup.select_one(selector)
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    break

            # Price - try multiple selectors
            price = None
            price_selectors = [
                ".pd__cost__retail-price",
                "[data-testid='pd-retail-price']",
                ".pd__cost",
                "span[class*='price']"
            ]
            for selector in price_selectors:
                price_tag = soup.select_one(selector)
                if price_tag:
                    price = price_tag.get_text(strip=True)
                    break

            # Description
            description = None
            desc_selectors = [
                "#information",
                ".pd__description",
                "[data-testid='product-description']"
            ]
            for selector in desc_selectors:
                desc_tag = soup.select_one(selector)
                if desc_tag:
                    description = desc_tag.get_text(" ", strip=True)
                    break

            # Nutrition table
            nutrition = {}
            nutrition_tables = soup.select("table.nutritionTable, table[class*='nutrition']")
            for table in nutrition_tables:
                rows = table.select("tr")
                for row in rows:
                    cols = row.select("td, th")
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        if key and value:
                            nutrition[key] = value

            return {
                "name": name,
                "price": price,
                "description": description,
                "nutrition": nutrition,
                "product_url": product_url,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to scrape product {product_url}: {e}")
            return None

    def scrape_category_bucket(self, category_name: str, url: str, max_products: int = 50):
        """Scrape a category and return up to max_products."""
        products = []

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = context.new_page()
                page.set_default_timeout(90000)

                logger.info(f"🛒 Scraping category: {category_name}")
                logger.info(f"   URL: {url}")

                # 1. Load category page
                logger.info("   📄 Loading category page...")
                page.goto(url, wait_until="domcontentloaded", timeout=90000)

                # 2. Accept cookies
                self._accept_cookies(page)

                # 3. Wait for page to stabilize
                logger.info("   ⏳ Waiting for page to load...")
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except:
                    logger.info("   ⚠️ Network didn't idle, continuing...")
                
                time.sleep(3)

                # 4. Scroll to trigger lazy loading
                logger.info("   📜 Scrolling to load products...")
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(1)
                
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)

                # 5. Wait for products
                self._wait_for_products(page)

                # 6. Parse the page
                logger.info("   🔍 Parsing product links...")
                soup = BeautifulSoup(page.content(), "html.parser")

                # 7. Find product links - try multiple strategies
                product_links = []
                
                # Strategy 1: Look for product tiles
                tiles = soup.select('article[data-testid="product-tile"]')
                logger.info(f"   Found {len(tiles)} product tiles")
                
                for tile in tiles:
                    link = tile.select_one("a[href*='/product/']")
                    if link:
                        href = link.get("href")
                        if href:
                            if not href.startswith("http"):
                                href = "https://www.sainsburys.co.uk" + href
                            if href not in product_links:
                                product_links.append(href)
                
                # Strategy 2: If no tiles, look for any product links
                if not product_links:
                    logger.info("   Trying alternate link strategy...")
                    all_links = soup.select('a[href*="/gol-ui/product/"]')
                    for link in all_links:
                        href = link.get("href")
                        if href and "/product/" in href:
                            if not href.startswith("http"):
                                href = "https://www.sainsburys.co.uk" + href
                            if href not in product_links:
                                product_links.append(href)

                # Limit to max_products
                product_links = product_links[:max_products]
                
                logger.info(f"   🔗 Found {len(product_links)} product pages to scrape")

                if not product_links:
                    logger.error("   ❌ No product links found!")
                    logger.info("   Saving page HTML for debugging...")
                    with open(f"debug_{category_name}.html", "w") as f:
                        f.write(page.content())
                    logger.info(f"   Saved to debug_{category_name}.html")

                # 8. Visit each product page
                for idx, link in enumerate(product_links, 1):
                    try:
                        logger.info(f"   📦 Scraping product {idx}/{len(product_links)}")
                        product = self._scrape_product_detail(page, link)
                        
                        if product and product.get("name") and product.get("price"):
                            products.append(product)
                            logger.info(f"      ✅ {product['name'][:50]}...")
                        else:
                            logger.warning(f"      ⚠️ Incomplete data for {link}")
                        
                        # Be polite - add delay
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        logger.warning(f"   ⚠️ Failed product {idx}: {e}")
                        continue

                browser.close()
                logger.info(f"✅ Scraped {len(products)} products from {category_name}")

            except Exception as e:
                logger.error(f"❌ Browser error: {e}")
                try:
                    browser.close()
                except:
                    pass

        return products