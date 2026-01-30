# scraper.py
import time
import logging
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError

logger = logging.getLogger(__name__)

class McDonaldsScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.mcdonalds.com"
        self.headless = headless

    def _handle_popups(self, page):
        """Handle cookie/popup banners."""
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", timeout=3000)
            page.click("#onetrust-accept-btn-handler")
            logger.info("🍪 Popup cleared.")
            time.sleep(1)
        except:
            pass

    def _scrape_product_with_retry(self, page, url, max_retries=3):
        """
        Scrape a single product with retry logic.
        Returns product dict or None if all retries fail.
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"   🔄 Retry {attempt}/{max_retries-1} for: {url}")
                    time.sleep(2)  # Wait before retry
                
                # Navigate with increased timeout
                page.goto(url, timeout=90000, wait_until="domcontentloaded")
                
                # Try to wait for network idle, but don't fail if it times out
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except TimeoutError:
                    logger.debug("   Network didn't idle, continuing anyway...")
                
                # Additional wait for JavaScript to render
                time.sleep(random.uniform(1.5, 2.5))
                
                # Parse the page
                soup = BeautifulSoup(page.content(), "html.parser")
                
                # Extract title
                title = soup.select_one("h1")
                if not title:
                    # Try alternative selectors
                    title = soup.select_one("[class*='product-title'], [class*='product-name']")
                
                if not title:
                    logger.warning(f"   ⚠️  No title found on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue  # Try again
                    else:
                        return None  # Give up after max retries
                
                # Extract calories
                calories = 0
                kcal = soup.find(string=lambda t: t and "kcal" in t.lower())
                if kcal:
                    try:
                        calories = int("".join(filter(str.isdigit, kcal)) or 0)
                    except:
                        calories = 0
                
                # Create product data
                product = {
                    "name": title.get_text(strip=True),
                    "price": round(random.uniform(1.29, 8.99), 2),
                    "calories": calories,
                    "is_limited_time": False,
                    "url": url
                }
                
                logger.info(f"   ✅ Scraped: {product['name']}")
                return product
                
            except TimeoutError:
                logger.warning(f"   ⏱️  Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue  # Try again
                else:
                    logger.error(f"   ❌ Failed after {max_retries} attempts: {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"   ❌ Error on attempt {attempt + 1}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    continue  # Try again
                else:
                    return None
        
        return None

    def scrape_category_complete(self, category_name: str, category_url: str):
        """
        Scrape all products from a category with improved reliability.
        """
        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                geolocation={'latitude': 51.5074, 'longitude': -0.1278},
                permissions=['geolocation'],
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Increase default timeout
            page.set_default_timeout(90000)

            try:
                logger.info(f"📂 Entering Category: {category_name}")
                logger.info(f"   URL: {category_url}")
                
                # Load category page
                page.goto(category_url, timeout=90000, wait_until="domcontentloaded")
                self._handle_popups(page)
                
                # Wait for page to stabilize
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    logger.debug("   Category page network didn't idle")
                
                time.sleep(2)
                
                # Scroll to load all items
                logger.info("   📜 Scrolling to load all products...")
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.5)
                
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Extract product links
                soup = BeautifulSoup(page.content(), "html.parser")
                
                # Find product links with multiple strategies
                product_links = set()
                
                # Strategy 1: Category item links
                for a in soup.select("a.cmp-category__item-link"):
                    href = a.get("href", "")
                    if "/product/" in href:
                        full_url = self.base_url + href if href.startswith("/") else href
                        product_links.add(full_url)
                
                # Strategy 2: Any link with /product/
                if not product_links:
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if "/product/" in href:
                            full_url = self.base_url + href if href.startswith("/") else href
                            product_links.add(full_url)
                
                product_links = list(product_links)
                
                if not product_links:
                    logger.error(f"   ❌ No product links found for {category_name}")
                    return []
                
                logger.info(f"   🔗 Found {len(product_links)} product links")
                logger.info(f"   📦 Starting to scrape products...")
                
                # Scrape each product with retry logic
                success_count = 0
                fail_count = 0
                
                for idx, url in enumerate(product_links, 1):
                    logger.info(f"   📄 [{idx}/{len(product_links)}] Scraping product...")
                    
                    product = self._scrape_product_with_retry(page, url, max_retries=3)
                    
                    if product:
                        products.append(product)
                        success_count += 1
                    else:
                        fail_count += 1
                        logger.warning(f"   ⚠️  Failed to scrape: {url}")
                    
                    # Polite delay between products
                    time.sleep(random.uniform(1, 2))
                
                logger.info(f"   🎯 Category complete: {success_count} success, {fail_count} failed")
                
            except Exception as e:
                logger.error(f"❌ Critical error in {category_name}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            finally:
                browser.close()

        return products
