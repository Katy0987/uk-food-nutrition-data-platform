"""
Enhanced Asda Scraper - Robust Product Data Extraction
Includes product name, price, and nutrition information
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

    def _accept_cookies(self, page):
        """Robust cookie acceptance."""
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", state="visible", timeout=5000)
            page.click("#onetrust-accept-btn-handler")
            logger.info("🍪 Cookie banner cleared.")
            time.sleep(1)
        except Exception:
            logger.debug("🍪 Cookie banner not found/already cleared.")

    def _extract_price(self, soup):
        """Multiple strategies to extract price."""
        price = None
        
        # Strategy 1: Look for common price selectors
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
        
        # Strategy 2: Find any element with £ symbol and reasonable length
        if not price:
            all_text_elements = soup.find_all(string=re.compile(r'£\d+\.?\d*'))
            for elem in all_text_elements:
                text = elem.strip()
                # Price should be £X.XX or £X format, not too long
                if len(text) < 15 and re.match(r'£\d+\.?\d{0,2}$', text):
                    price = text
                    break
        
        # Strategy 3: Look in meta tags
        if not price:
            meta_price = soup.find('meta', {'property': 'product:price:amount'})
            if meta_price and meta_price.get('content'):
                price = f"£{meta_price['content']}"
        
        return price

    def _extract_name(self, soup):
        """Multiple strategies to extract product name."""
        name = None
        
        # Strategy 1: H1 tag (most common)
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
        
        # Strategy 2: Look for product title in meta tags
        if not name:
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title and meta_title.get('content'):
                name = meta_title['content']
        
        # Strategy 3: Look for specific product title classes
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
        """Extract product category from breadcrumbs or page structure."""
        try:
            # Strategy 1: Breadcrumbs
            breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb', re.I))
            for breadcrumb in breadcrumbs:
                links = breadcrumb.find_all('a')
                if links:
                    # Get the last category before the product name (usually second to last link)
                    categories = [link.get_text(strip=True) for link in links]
                    if len(categories) >= 2:
                        # Return the most specific category (usually the last one)
                        return categories[-1].lower()
            
            # Strategy 2: Meta tags
            meta_category = soup.find('meta', {'property': 'product:category'})
            if meta_category and meta_category.get('content'):
                return meta_category['content'].lower()
            
            # Strategy 3: Look for category in URL or page data
            # This will be handled by URL checking
            
        except Exception as e:
            logger.debug(f"Could not extract category: {e}")
        
        return None
    
    def _extract_nutrition(self, soup):
        """Extract nutrition table information."""
        nutrition_data = {}
        
        try:
            # Look for nutrition table
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
            
            # Also look for nutrition in description/details sections
            if not nutrition_data:
                detail_sections = soup.find_all(['div', 'section'], class_=re.compile(r'(nutrition|detail|description)', re.I))
                for section in detail_sections:
                    text = section.get_text()
                    # Look for patterns like "Energy: 100kJ" or "Protein 5g"
                    nutrients = re.findall(r'(Energy|Protein|Fat|Carbohydrate|Sugar|Fibre|Salt|Sodium)[\s:]+([0-9.]+\s*[a-zA-Z]+)', text, re.I)
                    for nutrient, value in nutrients:
                        nutrition_data[nutrient.strip()] = value.strip()
        
        except Exception as e:
            logger.debug(f"Could not extract nutrition: {e}")
        
        return nutrition_data if nutrition_data else None

    def _scrape_product_detail(self, page, product_url, expected_category=None):
        """Visit product page to get Title, Price, and Nutrition.
        
        Args:
            page: Playwright page object
            product_url: URL of the product
            expected_category: The category we're scraping (for validation)
        """
        try:
            logger.debug(f"Visiting: {product_url}")
            
            # Navigate to the product page
            try:
                page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            except PlaywrightTimeout:
                logger.warning(f"⚠️ Timeout loading: {product_url}")
                return None
            
            # Wait for the page to stabilize
            time.sleep(random.uniform(1, 2))
            
            # Try to wait for product content (but don't fail if it times out)
            try:
                page.wait_for_selector("h1, [data-auto-id='productTitle']", timeout=5000)
            except:
                pass
            
            # Get the page content
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Extract data using multiple strategies
            name = self._extract_name(soup)
            price = self._extract_price(soup)
            nutrition = self._extract_nutrition(soup)
            
            # Extract category for validation
            product_category = self._extract_category(soup)
            
            # Validate category if expected_category is provided
            if expected_category and product_category:
                # Check if the product category matches the expected category
                # Use fuzzy matching (contains) to handle variations
                expected_lower = expected_category.lower()
                product_lower = product_category.lower()
                
                # Check for category match
                category_matches = (
                    expected_lower in product_lower or 
                    product_lower in expected_lower or
                    self._categories_match(expected_lower, product_lower)
                )
                
                if not category_matches:
                    logger.info(f"      ⏭️  Skipped: Wrong category (expected '{expected_category}', got '{product_category}')")
                    return None
            elif expected_category and not product_category:
                # Could not extract category - log but allow the product
                # (we don't want to reject products just because breadcrumbs are missing)
                logger.debug(f"      ℹ️  Could not extract category from product page")
            
            # Debug: Save page if extraction fails
            if not name or not price:
                logger.debug(f"Failed extraction - Name: {bool(name)}, Price: {bool(price)}")
                # Optionally save for debugging
                # with open(f"debug_product_{int(time.time())}.html", "w") as f:
                #     f.write(content)
            
            # Only return if we have at least name and price
            if name and price:
                product_data = {
                    "name": name,
                    "price": price,
                    "product_url": product_url,
                    "scraped_at": datetime.utcnow().isoformat()
                }
                
                # Add category if extracted
                if product_category:
                    product_data["detected_category"] = product_category
                
                # Add nutrition if available
                if nutrition:
                    product_data["nutrition"] = nutrition
                
                return product_data
            
            return None

        except Exception as e:
            logger.warning(f"⚠️ Error scraping {product_url}: {str(e)[:100]}")
            return None
    
    def _categories_match(self, cat1, cat2):
        """Check if two category strings are semantically similar."""
        # Define category synonyms and related terms
        category_groups = {
            'fruit': ['fruit', 'fruits'],
            'vegetable': ['vegetable', 'vegetables', 'veg', 'potatoes'],
            'meat': ['meat', 'poultry', 'chicken', 'beef', 'pork', 'lamb'],
            'fish': ['fish', 'seafood', 'salmon', 'tuna'],
            'bakery': ['bakery', 'bread', 'rolls', 'baked'],
            'dessert': ['dessert', 'desserts', 'cakes', 'sweet'],
            'dairy': ['dairy', 'milk', 'cheese', 'butter', 'cream', 'eggs', 'protein'],
            'sweets': ['sweets', 'chocolate', 'candy', 'confection'],
        }
        
        # Check if both categories belong to the same group
        for group_terms in category_groups.values():
            cat1_in_group = any(term in cat1 for term in group_terms)
            cat2_in_group = any(term in cat2 for term in group_terms)
            if cat1_in_group and cat2_in_group:
                return True
        
        return False

    def _is_valid_product_url(self, url, category_url=None):
        """Check if URL is likely a product page and matches the category.
        
        Args:
            url: The URL to check
            category_url: The category page URL (for extracting category path)
        """
        # Asda product URLs typically end with a product code or have specific patterns
        invalid_patterns = [
            '/aisle/', '/shelf/', '/recipes/', '/departments/',
            '/offers/', '/search/', '/favourites/', '/trolley/',
            '/account/', '/help/', '/store-locator/', '/blog/',
            '/george/', '/services/', '/money/', '/insurance/',
            '/deals/', '/inspiration/', '/special-offers/'
        ]
        
        # Must contain /groceries/
        if '/groceries/' not in url:
            return False
        
        # Must not contain invalid patterns
        for pattern in invalid_patterns:
            if pattern in url:
                return False
        
        # Should have some depth (not just category page)
        parts = url.split('/')
        if len(parts) < 6:  # Minimum depth for product pages
            return False
        
        # More flexible category filtering
        # Instead of requiring exact path match, check for related category keywords
        if category_url:
            category_info = self._extract_category_info(category_url)
            if category_info:
                # Check if URL contains any of the category keywords
                # This is more lenient than exact path matching
                category_keywords = category_info.get('keywords', [])
                if category_keywords:
                    # URL should contain at least one category keyword
                    # OR it should be a generic product URL (which we'll validate later by breadcrumbs)
                    url_lower = url.lower()
                    
                    # Allow generic /product/ URLs (we'll validate these with breadcrumbs)
                    if '/product/' in url_lower:
                        return True
                    
                    # Otherwise, check for category keywords
                    has_category_keyword = any(keyword in url_lower for keyword in category_keywords)
                    if not has_category_keyword:
                        # Also check if it's a subcategory (e.g., apples under fruit)
                        # Allow URLs that start with the main category path
                        main_category = category_info.get('main_category')
                        if main_category and main_category in url_lower:
                            return True
                        return False
        
        return True
    
    def _extract_category_info(self, category_url):
        """Extract category information from the category URL.
        
        Returns a dict with category keywords for flexible matching.
        Example: 
            Input: "https://www.asda.com/groceries/fruit-veg-flowers/fruit"
            Output: {
                'main_category': 'fruit',
                'parent_category': 'fruit-veg-flowers', 
                'keywords': ['fruit', 'veg', 'flowers']
            }
        """
        try:
            # Remove query parameters and fragments
            clean_url = category_url.split('?')[0].split('#')[0]
            
            # Find the part after /groceries/
            if '/groceries/' in clean_url:
                parts = clean_url.split('/groceries/')
                if len(parts) > 1:
                    category_path = parts[1].strip('/')
                    path_parts = category_path.split('/')
                    
                    # Extract keywords from the path
                    keywords = []
                    for part in path_parts:
                        # Split by dash and add individual words
                        keywords.extend(part.split('-'))
                    
                    return {
                        'main_category': path_parts[-1] if path_parts else None,
                        'parent_category': path_parts[0] if path_parts else None,
                        'keywords': list(set(keywords)),  # Remove duplicates
                        'full_path': category_path
                    }
        except:
            pass
        
        return None

    def scrape_category_bucket(self, category_name: str, url: str, max_products: int = 50):
        """Scrape products from a category page.
        
        Args:
            category_name: Name of the category being scraped
            url: Category page URL
            max_products: Maximum number of products to scrape
        """
        products = []
        
        with sync_playwright() as p:
            # Launch browser with more realistic settings
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
                
                # Handle cookies
                self._accept_cookies(page)
                
                # Wait for initial content
                time.sleep(2)
                
                # Aggressive scrolling to load all products
                logger.info("   📜 Scrolling to load products...")
                for i in range(8):  # Increased scroll attempts
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.8)
                
                # Scroll back to top to ensure all content is in DOM
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                # Get all links from the page
                content = page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # Extract category info for filtering
                category_info = self._extract_category_info(url)
                if category_info:
                    logger.info(f"   🔍 Category filter - Keywords: {', '.join(category_info['keywords'][:5])}")
                else:
                    logger.info(f"   🔍 Category filter - Using breadcrumb validation only")
                
                # Find product links
                found_links = set()
                all_links = soup.find_all("a", href=True)
                
                logger.info(f"   🔍 Analyzing {len(all_links)} links...")
                
                for link in all_links:
                    href = link['href']
                    
                    # Make full URL
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Validate if it's a product URL with category filtering
                    if self._is_valid_product_url(full_url, category_url=url):
                        # Remove query parameters and fragments for deduplication
                        clean_url = full_url.split('?')[0].split('#')[0]
                        found_links.add(clean_url)
                
                product_links = list(found_links)[:max_products * 2]  # Get extra in case some fail
                
                if not product_links:
                    logger.error(f"   ❌ No product links found for {category_name}")
                    # Save debug HTML
                    debug_filename = f"debug_asda_{category_name}_{int(time.time())}.html"
                    with open(debug_filename, "w", encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"   💾 Saved debug HTML to {debug_filename}")
                    return []
                
                logger.info(f"   🔗 Found {len(product_links)} potential product links (filtered by category)")
                logger.info(f"   📦 Starting to scrape products...")
                
                # Scrape each product with category validation
                success_count = 0
                skip_count = 0
                
                for idx, link in enumerate(product_links, 1):
                    # Stop if we have enough successful scrapes
                    if success_count >= max_products:
                        logger.info(f"   ✅ Reached target of {max_products} products")
                        break
                    
                    logger.info(f"   📦 [{idx}/{len(product_links)}] Scraping...")
                    
                    # Pass expected category for validation
                    item_data = self._scrape_product_detail(page, link, expected_category=category_name)
                    
                    if item_data:
                        products.append(item_data)
                        success_count += 1
                        name_preview = item_data['name'][:40] + "..." if len(item_data['name']) > 40 else item_data['name']
                        logger.info(f"      ✅ Got: {name_preview} ({item_data['price']})")
                        
                        if item_data.get('nutrition'):
                            logger.info(f"         📊 Nutrition: {len(item_data['nutrition'])} fields")
                    else:
                        skip_count += 1
                        # Don't log every skip to reduce noise
                        if skip_count <= 5:
                            logger.debug(f"      ⚠️  Skipped (No data extracted or wrong category)")
                    
                    # Polite delay
                    time.sleep(random.uniform(0.8, 1.5))

                logger.info(f"   🎯 Successfully scraped {len(products)} products from {category_name}")
                if skip_count > 0:
                    logger.info(f"   ⏭️  Skipped {skip_count} items (wrong category or extraction failed)")

            except Exception as e:
                logger.error(f"❌ Critical Error in {category_name}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                browser.close()

        return products