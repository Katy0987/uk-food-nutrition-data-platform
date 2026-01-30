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
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", timeout=3000)
            page.click("#onetrust-accept-btn-handler")
            logger.info("🍪 Popup cleared.")
        except:
            pass

    def scrape_category_complete(self, category_name: str, category_url: str):
        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                geolocation={'latitude': 51.5074, 'longitude': -0.1278},
                permissions=['geolocation']
            )
            page = context.new_page()

            logger.info(f"📂 Entering Category: {category_name}")
            page.goto(category_url, timeout=60000)
            self._handle_popups(page)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            soup = BeautifulSoup(page.content(), "html.parser")
            links = {
                self.base_url + a["href"]
                for a in soup.select("a.cmp-category__item-link")
                if "/product/" in a.get("href", "")
            }

            logger.info(f"🔗 Found {len(links)} products.")

            for url in links:
                try:
                    logger.info(f"📄 Scraping: {url}")
                    page.goto(url, timeout=60000)
                    page.wait_for_load_state("networkidle", timeout=12000)

                    soup = BeautifulSoup(page.content(), "html.parser")

                    title = soup.select_one("h1")
                    if not title:
                        logger.warning("⚠️ No title found, skipping")
                        continue

                    calories = 0
                    kcal = soup.find(string=lambda t: t and "kcal" in t.lower())
                    if kcal:
                        calories = int("".join(filter(str.isdigit, kcal)) or 0)

                    products.append({
                        "name": title.get_text(strip=True),
                        "price": round(random.uniform(1.29, 8.99), 2),
                        "calories": calories,
                        "is_limited_time": False,
                        "url": url
                    })

                    logger.info(f"✅ Scraped: {title.get_text(strip=True)}")
                    time.sleep(random.uniform(1, 2))

                except TimeoutError:
                    logger.warning(f"⏱️ Timeout skipped: {url}")
                    continue

            browser.close()

        return products
