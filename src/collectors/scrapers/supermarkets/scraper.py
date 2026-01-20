import time
import logging
import random
from typing import List, Dict, Optional
from bs4 import BeautifulSoup # type: ignore
from playwright.sync_api import sync_playwright # type: ignore

logger = logging.getLogger(__name__)

class TescoScraper:
    def __init__(self, headless: bool = False): # Default to False so you can see it
        self.headless = headless

    def _apply_stealth(self, page):
        """Hides the 'navigator.webdriver' flag."""
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    def _accept_cookies(self, page):
        try:
            selector = "button:has-text('Accept all')"
            page.wait_for_selector(selector, timeout=5000)
            page.click(selector)
            logger.info("🍪 Cookie banner accepted.")
            time.sleep(1.5) 
        except Exception:
            logger.info("ℹ️ Cookie banner not found.")

    def scrape_category_with_pagination(self, url: str, category: str, max_pages: int = 3) -> List[Dict]:
        all_products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-http2', 
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-GB,en;q=0.9",
                    "Referer": "https://www.google.com/"
                }
            )
            
            page = context.new_page()
            self._apply_stealth(page)

            current_page = 1
            while current_page <= max_pages:
                full_url = f"{url}?page={current_page}"
                logger.info(f"📄 Scraping {category} - Page {current_page}")
                products_on_page = self._parse_html(soup, category)

                if not products_on_page:
                    logger.info(f"Reached the end of available products for {category} at page {current_page}.")
                    break

                try:
                    # 1. Load Page
                    page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
                    
                    # 2. Check for Security Check
                    if "security checks" in page.content().lower():
                        print(f"\n🚨 BLOCK DETECTED ON {category}. PLEASE SOLVE MANUALLY IN BROWSER.")
                        try:
                            # Wait up to 60s for you to solve it
                            page.wait_for_selector("li[data-testid='product-line']", timeout=60000)
                            print("✅ Block cleared!")
                        except:
                            logger.error("❌ Failed to clear block.")
                            break

                    time.sleep(random.uniform(2, 4))

                    # 3. Cookies
                    if current_page == 1:
                        self._accept_cookies(page)

                    # 4. Wait for Content
                    html = ""  # Pre-define html so it exists even if the wait fails
                    try:
                        # Increased timeout slightly for slow categories
                        page.wait_for_selector("li[data-testid='product-line'], .product-list--list-item", timeout=15000)
                        html = page.content()
                    except Exception:
                        logger.warning(f"⚠️ Timeout: Products didn't appear on page {current_page}. It might be a slow load or a block.")
                        # If the page is totally blank or blocked, stop this category
                        if "security checks" in page.content().lower():
                            break
                        else:
                            # If it's just an empty category, we move to the next
                            current_page += 1
                            continue

                    # 5. Parse (Only if we have HTML)
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        products = self._parse_html(soup, category)
                        
                        if not products:
                            logger.info("🔚 No more products found. Finishing category.")
                            break
                            
                        all_products.extend(products)
                        logger.info(f"✅ Found {len(products)} items.")
                        current_page += 1
                    else:
                        break # Exit loop if no HTML was captured
                except Exception as e:
                    logger.error(f" Error: {e}")
                    break
            browser.close()
        return all_products

    def _parse_html(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        products = []
        # Target the list items using data-testid first
        items = soup.find_all('li', {'data-testid': 'product-line'})
        if not items:
            items = soup.find_all('li', class_='product-list--list-item')

        for item in items:
            try:
                name_tag = item.find('h3')
                if not name_tag: continue
                
                price_tag = item.select_one("[data-testid='price'], .beans-price__text")
                price = 0.0
                if price_tag:
                    raw_price = price_tag.get_text(strip=True).replace('£', '').split()[0]
                    try: price = float(raw_price)
                    except: pass

                link_tag = item.find('a', href=True)
                url = "https://www.tesco.com" + link_tag['href'] if link_tag else None

                products.append({
                    "name": name_tag.get_text(strip=True),
                    "price": price,
                    "category": category,
                    "url": url
                })
            except: continue
        return products