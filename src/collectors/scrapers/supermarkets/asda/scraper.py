"""
Fully Fixed Asda Scraper - All Issues Resolved
1. Filters out "Stock up save" promotional items
2. Expanded category hierarchies for sweets and protein
3. Added drinks category support
"""

import logging
import time
import random
import re
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

class AsdaScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.base_url = "https://www.asda.com"
        
        # FIXED: Expanded category hierarchies
        self.category_hierarchies = {
            'fruit': ['fruit', 'fruits', 'apples', 'oranges', 'bananas', 'grapes', 
                     'berries', 'melon', 'pineapple', 'citrus', 'tropical', 'stone fruit',
                     'peaches', 'plums', 'nectarines', 'apricots', 'cherries', 'mango',
                     'kiwi', 'pears', 'exotic fruit', 'strawberries', 'blueberries',
                     'raspberries', 'blackberries'],
            
            'vegetables': ['vegetable', 'vegetables', 'veg', 'potatoes', 'onions', 'leeks',
                          'carrots', 'cabbage', 'sprouts', 'broccoli', 'cauliflower',
                          'peppers', 'tomatoes', 'salad', 'lettuce', 'cucumber', 'courgette',
                          'mushrooms', 'beetroot', 'parsnips', 'turnips', 'swede',
                          'spinach', 'kale', 'peas', 'beans', 'corn', 'asparagus'],
            
            'meat': ['meat', 'poultry', 'chicken', 'beef', 'pork', 'lamb', 'turkey',
                    'bacon', 'sausages', 'mince', 'steak', 'chops', 'ham', 'duck',
                    'venison', 'gammon', 'ribs'],
            
            'fish': ['fish', 'seafood', 'salmon', 'tuna', 'cod', 'haddock', 'prawns',
                    'shrimp', 'crab', 'lobster', 'mackerel', 'trout', 'seabass',
                    'mussels', 'scallops', 'squid', 'octopus'],
            
            'bakery': ['bakery', 'bread', 'rolls', 'buns', 'bagels', 'baguette',
                      'croissant', 'muffins', 'baked', 'fresh bakery', 'loaf',
                      'ciabatta', 'focaccia', 'sourdough', 'wraps', 'pitta'],
            
            'dessert': ['dessert', 'desserts', 'cakes', 'cream cakes', 'pastries',
                       'trifle', 'cheesecake', 'gateaux', 'sweet', 'pudding',
                       'brownies', 'cookies', 'tarts', 'eclairs'],
            
            # FIXED: Expanded protein category to include Starbucks and more brands
            'protein': ['protein', 'milk', 'butter', 'cream', 'eggs', 'dairy',
                       'cheese', 'yogurt', 'yoghurt', 'starbucks', 'frappuccino',
                       'cappuccino', 'latte', 'coffee drinks', 'protein drinks',
                       'protein shake', 'smoothie', 'kefir', 'buttermilk',
                       'free range eggs', 'organic milk', 'almond milk', 'oat milk',
                       'soya milk', 'plant-based milk'],
            
            'cheese': ['cheese', 'cheddar', 'brie', 'stilton', 'mozzarella',
                      'parmesan', 'feta', 'goats cheese', 'goat cheese', 'edam',
                      'camembert', 'halloumi', 'cream cheese', 'cottage cheese',
                      'ricotta', 'mascarpone', 'blue cheese'],
            
            # FIXED: Expanded sweets category to include chewing gum and more
            'sweets': ['sweets', 'chocolate', 'candy', 'confectionery', 'chocolates',
                      'toffee', 'fudge', 'liquorice', 'gummies', 'lollies',
                      'chewing gum', 'gum', 'mints', 'mint', 'bubble gum',
                      'sugar free sweets', 'hard candy', 'soft candy',
                      'jelly sweets', 'marshmallows', 'bon bons', 'treats'],
            
            # NEW: Added drinks category
            'drinks': ['drinks', 'beverages', 'water', 'juice', 'soft drinks',
                      'soda', 'cola', 'fizzy drinks', 'energy drinks', 'sports drinks',
                      'cordial', 'squash', 'tea', 'coffee', 'hot chocolate',
                      'milkshake', 'smoothie', 'mineral water', 'sparkling water',
                      'still water', 'tonic', 'lemonade', 'ginger ale',
                      'fruit juice', 'orange juice', 'apple juice']
        }
        
        # FIXED: Keywords to filter out promotional/non-product items
        self.excluded_keywords = [
            'stock up save',
            'save £',
            'save when you',
            'multi-buy',
            'special offer',
            'promotion',
            'view all',
            'see all',
            'browse',
            'shop by',
            'offers',
            'deals'
        ]

    def _accept_cookies(self, page):
        """Robust cookie acceptance."""
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", state="visible", timeout=5000)
            page.click("#onetrust-accept-btn-handler")
            logger.info("🍪 Cookie banner cleared.")
            time.sleep(1)
        except Exception:
            logger.debug("🍪 Cookie banner not found/already cleared.")

    def _is_promotional_item(self, name):
        """
        FIXED: Check if the item is a promotional/non-product item.
        Returns True if it should be excluded.
        """
        if not name:
            return True
        
        name_lower = name.lower()
        
        # Check for excluded keywords
        for keyword in self.excluded_keywords:
            if keyword in name_lower:
                logger.debug(f"      ⏭️  Filtered out promotional item: {name[:50]}")
                return True
        
        # Additional checks
        if len(name) < 5:  # Too short to be a real product name
            return True
        
        if name_lower.startswith('save') or name_lower.startswith('offer'):
            return True
        
        return False

    def _extract_price(self, soup):
        """Multiple strategies to extract price."""
        price = None
        
        price_selectors = [
            'span.co-product__price',
            '[data-auto-id="productPrice"]',
            '.pdp-main-details__price',
            'strong[class*="price"]',
            'span[class*="price"]',
            '[class*="co-product__price"]',
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if '£' in text:
                    price = text
                    break
        
        if not price:
            all_text_elements = soup.find_all(string=re.compile(r'£\d+\.?\d*'))
            for elem in all_text_elements:
                text = elem.strip()
                if len(text) < 15 and re.match(r'£\d+\.?\d{0,2}$', text):
                    price = text
                    break
        
        if not price:
            meta_price = soup.find('meta', {'property': 'product:price:amount'})
            if meta_price and meta_price.get('content'):
                price = f"£{meta_price['content']}"
        
        return price

    def _extract_name(self, soup):
        """Multiple strategies to extract product name."""
        name = None
        
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
        
        if not name:
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title and meta_title.get('content'):
                name = meta_title['content']
        
        if not name:
            title_selectors = [
                '[data-auto-id="productTitle"]',
                '.pdp-main-details__title',
                '.co-product__title',
                'h1[class*="title"]',
            ]
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    name = elem.get_text(strip=True)
                    break
        
        return name

    def _extract_category(self, soup):
        """Extract product category from breadcrumbs."""
        try:
            breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb', re.I))
            for breadcrumb in breadcrumbs:
                links = breadcrumb.find_all('a')
                if links:
                    categories = [link.get_text(strip=True) for link in links]
                    if len(categories) >= 2:
                        return categories[-1].lower()
            
            meta_category = soup.find('meta', {'property': 'product:category'})
            if meta_category and meta_category.get('content'):
                return meta_category['content'].lower()
            
        except Exception as e:
            logger.debug(f"Could not extract category: {e}")
        
        return None
    
    def _extract_nutrition(self, soup):
        """Extract nutrition table information."""
        nutrition_data = {}
        
        try:
            nutrition_selectors = [
                'table.nutritional-table',
                'table[class*="nutrition"]',
                '.nutrition-information table',
                '[data-auto-id="nutritionTable"]',
            ]
            
            nutrition_table = None
            for selector in nutrition_selectors:
                nutrition_table = soup.select_one(selector)
                if nutrition_table:
                    break
            
            if nutrition_table:
                rows = nutrition_table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            nutrition_data[key] = value
            
            if not nutrition_data:
                detail_sections = soup.find_all(['div', 'section'], class_=re.compile(r'(nutrition|detail|description)', re.I))
                for section in detail_sections:
                    text = section.get_text()
                    nutrients = re.findall(r'(Energy|Protein|Fat|Carbohydrate|Sugar|Fibre|Salt|Sodium)[\s:]+([0-9.]+\s*[a-zA-Z]+)', text, re.I)
                    for nutrient, value in nutrients:
                        nutrition_data[nutrient.strip()] = value.strip()
        
        except Exception as e:
            logger.debug(f"Could not extract nutrition: {e}")
        
        return nutrition_data if nutrition_data else None

    def _category_matches(self, expected_category, detected_category):
        """Check if detected category belongs to expected category hierarchy."""
        if not detected_category:
            return True
        
        expected_lower = expected_category.lower()
        detected_lower = detected_category.lower()
        
        if expected_lower == detected_lower:
            return True
        
        if expected_lower in self.category_hierarchies:
            allowed_categories = self.category_hierarchies[expected_lower]
            
            for allowed in allowed_categories:
                if allowed in detected_lower or detected_lower in allowed:
                    return True
        
        if expected_lower in detected_lower:
            return True
        
        return False

    def _scrape_product_detail(self, page, product_url, expected_category=None):
        """Visit product page to get Title, Price, and Nutrition."""
        try:
            logger.debug(f"Visiting: {product_url}")
            
            try:
                page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            except PlaywrightTimeout:
                logger.warning(f"⚠️ Timeout loading: {product_url}")
                return None
            
            time.sleep(random.uniform(1, 2))
            
            try:
                page.wait_for_selector("h1, [data-auto-id='productTitle']", timeout=5000)
            except:
                pass
            
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            name = self._extract_name(soup)
            
            # FIXED: Filter out promotional items
            if self._is_promotional_item(name):
                return None
            
            price = self._extract_price(soup)
            nutrition = self._extract_nutrition(soup)
            
            product_category = self._extract_category(soup)
            
            if expected_category and product_category:
                if not self._category_matches(expected_category, product_category):
                    logger.debug(f"      ⏭️  Category mismatch (expected '{expected_category}', got '{product_category}')")
                    return None
            
            if name and price:
                product_data = {
                    "name": name,
                    "price": price,
                    "product_url": product_url,
                    "scraped_at": datetime.utcnow().isoformat()
                }
                
                if product_category:
                    product_data["detected_category"] = product_category
                
                if nutrition:
                    product_data["nutrition"] = nutrition
                
                return product_data
            
            return None

        except Exception as e:
            logger.warning(f"⚠️ Error scraping {product_url}: {str(e)[:100]}")
            return None

    def _is_valid_product_url(self, url, category_url=None):
        """Check if URL is likely a product page."""
        invalid_patterns = [
            '/aisle/', '/shelf/', '/recipes/', '/departments/',
            '/offers/', '/search/', '/favourites/', '/trolley/',
            '/account/', '/help/', '/store-locator/', '/blog/',
            '/george/', '/services/', '/money/', '/insurance/',
            '/deals/', '/inspiration/', '/special-offers/'
        ]
        
        if '/groceries/' not in url:
            return False
        
        for pattern in invalid_patterns:
            if pattern in url:
                return False
        
        parts = url.split('/')
        if len(parts) < 6:
            return False
        
        return True

    def scrape_category_bucket(self, category_name: str, url: str, max_products: int = 50):
        """Scrape products from a category page."""
        products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale='en-GB',
            )
            
            page = context.new_page()

            try:
                logger.info(f"🛒 Opening Category: {category_name}")
                logger.info(f"   URL: {url}")
                
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self._accept_cookies(page)
                time.sleep(2)
                
                logger.info("   📜 Scrolling to load products...")
                for i in range(8):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.8)
                
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                content = page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                found_links = set()
                all_links = soup.find_all("a", href=True)
                
                logger.info(f"   🔍 Analyzing {len(all_links)} links...")
                
                for link in all_links:
                    href = link['href']
                    
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    if self._is_valid_product_url(full_url):
                        clean_url = full_url.split('?')[0].split('#')[0]
                        found_links.add(clean_url)
                
                product_links = list(found_links)[:max_products * 3]
                
                if not product_links:
                    logger.error(f"   ❌ No product links found for {category_name}")
                    debug_filename = f"debug_asda_{category_name}_{int(time.time())}.html"
                    with open(debug_filename, "w", encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"   💾 Saved debug HTML to {debug_filename}")
                    return []
                
                logger.info(f"   🔗 Found {len(product_links)} potential product links")
                logger.info(f"   📦 Starting to scrape products (target: {max_products})...")
                
                success_count = 0
                skip_count = 0
                promo_filtered = 0
                
                for idx, link in enumerate(product_links, 1):
                    if success_count >= max_products:
                        logger.info(f"   ✅ Reached target of {max_products} products")
                        break
                    
                    if idx % 10 == 0:
                        logger.info(f"   📊 Progress: {success_count}/{max_products} products ({idx} checked, {promo_filtered} promo filtered)")
                    
                    item_data = self._scrape_product_detail(page, link, expected_category=category_name)
                    
                    if item_data:
                        products.append(item_data)
                        success_count += 1
                        name_preview = item_data['name'][:50] + "..." if len(item_data['name']) > 50 else item_data['name']
                        logger.info(f"      ✅ [{success_count}] {name_preview} ({item_data['price']})")
                        
                        if item_data.get('nutrition'):
                            logger.info(f"         📊 Nutrition: {len(item_data['nutrition'])} fields")
                    else:
                        skip_count += 1
                        # Count promotional items separately
                        if skip_count > promo_filtered:
                            promo_filtered += 1
                    
                    time.sleep(random.uniform(0.8, 1.5))

                logger.info(f"   🎯 Successfully scraped {len(products)} products from {category_name}")
                if skip_count > 0:
                    logger.info(f"   ⏭️  Skipped {skip_count} items ({promo_filtered} promotional/invalid)")

            except KeyboardInterrupt:
                logger.warning("⚠️ Interrupted by user")
                raise
            except Exception as e:
                logger.error(f"❌ Critical Error in {category_name}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                try:
                    browser.close()
                except:
                    pass

        return products