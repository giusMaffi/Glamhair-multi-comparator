#!/usr/bin/env python3
"""
PDP (Product Detail Page) Scraper - WITH PRICE EXTRACTION
==========================================================
Purpose: Enrich product dataset with detailed info from PDPs
Author: Peppe
Date: 2026-01-20

Extracts from each PDP:
- Detailed description
- Ingredients/INCI
- Usage instructions
- Benefits/claims
- Technologies
- Nutritional values (supplements)
- **PRICES** (regular price, promo price, discount) ← NEW!

Output: Enriched ALL_PRODUCTS.json with full product details
"""

import json
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ============================================
# CONFIGURATION
# ============================================

# Get project root (3 levels up from scripts/scraping/scrape_pdp.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
INPUT_FILE = DATA_DIR / 'products' / 'ALL_PRODUCTS.json'
OUTPUT_FILE = DATA_DIR / 'products' / 'ALL_PRODUCTS_ENRICHED.json'
BACKUP_FILE = DATA_DIR / 'products' / 'ALL_PRODUCTS_BEFORE_PDP.json'

# Scraping settings
DELAY_BETWEEN_REQUESTS = 2  # seconds (be nice to server)
MAX_RETRIES = 3
TIMEOUT = 10  # seconds

# ============================================
# PRICE EXTRACTION CLASS
# ============================================

class PriceExtractor:
    """Extract prices from product HTML pages"""
    
    def __init__(self):
        """Initialize price extraction patterns"""
        # Regex pattern for price matching (supports both comma and dot)
        self.price_pattern = re.compile(r'(\d+[,\.]\d{2})\s*€')
        
        # CSS selectors for price elements (ordered by priority)
        self.price_selectors = {
            'regular': [
                '.regular-price',
                '.old-price',
                '.product-price .regular-price',
                'span.regular-price',
                'div.regular-price',
            ],
            'current': [
                '.price:not(.regular-price)',
                '.product-price .price',
                '.current-price',
                'span.price',
                'div.price',
            ],
            'discount': [
                '.discount',
                '.discount-percentage',
                '.discount-amount',
                'span.discount',
            ]
        }
    
    def extract_prices(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """
        Extract regular and promotional prices from product page
        
        Returns:
            Dictionary with 'regular_price', 'promo_price', 'discount_percent'
        """
        result = {
            'regular_price': None,
            'promo_price': None,
            'discount_percent': None
        }
        
        # Strategy 1: Try structured CSS selectors
        prices = self._extract_with_selectors(soup)
        
        if prices['regular_price'] or prices['promo_price']:
            return prices
        
        # Strategy 2: Fallback to pattern matching in page text
        return self._extract_with_patterns(soup)
    
    def _extract_with_selectors(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extract prices using CSS selectors"""
        result = {
            'regular_price': None,
            'promo_price': None,
            'discount_percent': None
        }
        
        # Try to find regular price
        for selector in self.price_selectors['regular']:
            elem = soup.select_one(selector)
            if elem:
                price = self._parse_price(elem.get_text(strip=True))
                if price:
                    result['regular_price'] = price
                    break
        
        # Try to find current/promotional price
        for selector in self.price_selectors['current']:
            elem = soup.select_one(selector)
            if elem:
                price = self._parse_price(elem.get_text(strip=True))
                if price:
                    result['promo_price'] = price
                    break
        
        # Try to find discount percentage
        for selector in self.price_selectors['discount']:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                discount = self._parse_discount(text)
                if discount:
                    result['discount_percent'] = discount
                    break
        
        # If we found promo_price but no regular_price, 
        # promo_price might actually be the regular price
        if result['promo_price'] and not result['regular_price']:
            if not result['discount_percent']:  # No discount indicator
                result['regular_price'] = result['promo_price']
                result['promo_price'] = None
        
        return result
    
    def _extract_with_patterns(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Fallback: Extract prices using regex patterns"""
        result = {
            'regular_price': None,
            'promo_price': None,
            'discount_percent': None
        }
        
        # Get all text from page
        page_text = soup.get_text()
        
        # Find all prices
        price_matches = self.price_pattern.findall(page_text)
        
        if len(price_matches) >= 2:
            # Assume first is regular, second is promo
            result['regular_price'] = self._parse_price(price_matches[0])
            result['promo_price'] = self._parse_price(price_matches[1])
        elif len(price_matches) == 1:
            # Only one price found - it's the regular price
            result['regular_price'] = self._parse_price(price_matches[0])
        
        # Look for discount percentage
        discount_pattern = re.compile(r'-\s*(\d+)\s*%')
        discount_match = discount_pattern.search(page_text)
        if discount_match:
            result['discount_percent'] = int(discount_match.group(1))
        
        return result
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price string to float"""
        if not price_text:
            return None
        
        # Remove currency symbols and whitespace
        clean_text = price_text.replace('€', '').strip()
        
        try:
            # Replace comma with dot for float conversion
            clean_text = clean_text.replace(',', '.')
            return float(clean_text)
        except (ValueError, AttributeError):
            return None
    
    def _parse_discount(self, discount_text: str) -> Optional[int]:
        """Parse discount percentage string"""
        if not discount_text:
            return None
        
        # Extract number from discount text
        pattern = re.compile(r'(\d+)\s*%')
        match = pattern.search(discount_text)
        
        if match:
            return int(match.group(1))
        return None

# ============================================
# SELENIUM SETUP
# ============================================

def setup_driver():
    """Setup headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ============================================
# CONTENT EXTRACTION
# ============================================

def extract_description_tab(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract content from 'Descrizione' tab
    
    This tab contains rich product information including:
    - Product description
    - Ingredients
    - Usage instructions
    - Benefits
    """
    
    result = {
        'descrizione_completa': '',
        'ingredienti': '',
        'modo_uso': '',
        'benefici': '',
        'tecnologie': ''
    }
    
    # Find description tab content
    # Common selectors for description tab
    desc_selectors = [
        '#description',
        'div[id="description"]',
        '.product-description',
        '[itemprop="description"]'
    ]
    
    description_div = None
    for selector in desc_selectors:
        description_div = soup.select_one(selector)
        if description_div:
            break
    
    if not description_div:
        return result
    
    # Get full text
    full_text = description_div.get_text(separator=' ', strip=True)
    result['descrizione_completa'] = full_text
    
    # Try to extract structured info
    text_lower = full_text.lower()
    
    # Extract ingredients
    ingredienti_patterns = [
        r'ingredienti[:\s]+([^\.]+)',
        r'inci[:\s]+([^\.]+)',
        r'formulato con[:\s]+([^\.]+)',
        r'contiene[:\s]+([^\.]+)',
        r'ingredients[:\s]+([^\.]+)'
    ]
    
    for pattern in ingredienti_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            result['ingredienti'] = match.group(1).strip()
            break
    
    # Extract usage instructions
    uso_patterns = [
        r'(?:applicazione|modo d.uso|come usare|utilizzo)[:\s]+([^\.]+(?:\.[^\.]+){0,2})',
        r'(?:apply|application|how to use)[:\s]+([^\.]+(?:\.[^\.]+){0,2})'
    ]
    
    for pattern in uso_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            result['modo_uso'] = match.group(1).strip()
            break
    
    # Extract benefits
    benefici_keywords = ['benefici', 'risultati', 'effetti', 'benefits', 'azione']
    for keyword in benefici_keywords:
        if keyword in text_lower:
            # Extract sentence containing keyword
            sentences = full_text.split('.')
            for sent in sentences:
                if keyword in sent.lower():
                    result['benefici'] += sent.strip() + '. '
    
    # Extract technologies (brand-specific keywords)
    tech_keywords = [
        'abissina', 'acido ialuronico', 'vitamina e', 'keratina',
        'olio di macadamia', 'caviale', 'collagene', 'biotina',
        'omega 3', 'omega 5', 'omega 7', 'proteine vegetali'
    ]
    
    found_tech = []
    for tech in tech_keywords:
        if tech in text_lower:
            found_tech.append(tech.title())
    
    result['tecnologie'] = ', '.join(found_tech) if found_tech else ''
    
    return result

def extract_nutritional_values(soup: BeautifulSoup) -> str:
    """
    Extract nutritional values (for supplements)
    Usually in 'Valori nutrizionali' tab
    """
    
    # Look for nutritional table
    nutritional_selectors = [
        '#extra-0',  # Common for nutrition tab
        'div[id*="nutri"]',
        'table[class*="nutri"]',
        '.nutritional-values'
    ]
    
    for selector in nutritional_selectors:
        elem = soup.select_one(selector)
        if elem:
            # Extract table or text
            text = elem.get_text(separator='\n', strip=True)
            if text and len(text) > 10:
                return text
    
    return ''

def extract_pdp_data(driver: webdriver.Chrome, url: str, price_extractor: PriceExtractor) -> Dict:
    """
    Fetch PDP and extract all relevant data INCLUDING PRICES
    """
    
    try:
        driver.get(url)
        
        # Wait for page load
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Small delay for dynamic content
        time.sleep(1)
        
        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract data
        data = {
            'pdp_scraped': True,
            'pdp_scraped_at': datetime.now().isoformat()
        }
        
        # Description tab
        desc_data = extract_description_tab(soup)
        data.update(desc_data)
        
        # Nutritional values (if present)
        nutri = extract_nutritional_values(soup)
        if nutri:
            data['valori_nutrizionali'] = nutri
        
        # ⭐ PRICES - NEW!
        price_data = price_extractor.extract_prices(soup)
        data.update(price_data)
        
        return data
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {
            'pdp_scraped': False,
            'pdp_error': str(e)
        }

# ============================================
# MAIN SCRAPING LOGIC
# ============================================

def scrape_all_pdps(products: List[Dict], driver: webdriver.Chrome):
    """
    Scrape all PDPs and enrich products
    """
    
    total = len(products)
    enriched = 0
    errors = 0
    
    # Initialize price extractor
    price_extractor = PriceExtractor()
    
    print(f"\n🔍 Starting PDP scraping...")
    print(f"   Total products: {total}")
    print(f"   Estimated time: {total * (DELAY_BETWEEN_REQUESTS + 2) / 60:.0f} minutes")
    print("-" * 70)
    
    start_time = time.time()
    
    for idx, product in enumerate(products, 1):
        url = product.get('url', '')
        
        if not url:
            print(f"\n❌ Product {idx}/{total}: No URL")
            errors += 1
            continue
        
        # Progress
        elapsed = time.time() - start_time
        if idx > 1:
            avg_time = elapsed / (idx - 1)
            eta_seconds = avg_time * (total - idx + 1)
            eta_minutes = eta_seconds / 60
            print(f"\n📦 Product {idx}/{total} ({idx/total*100:.1f}%) - ETA: {eta_minutes:.0f}min")
        else:
            print(f"\n📦 Product {idx}/{total}")
        
        print(f"   {product['brand']} - {product['nome'][:50]}...")
        print(f"   URL: {url}")
        
        # Try to scrape with retries
        attempt = 0
        success = False
        
        while attempt < MAX_RETRIES and not success:
            attempt += 1
            
            if attempt > 1:
                print(f"   🔄 Retry {attempt}/{MAX_RETRIES}")
            
            try:
                pdp_data = extract_pdp_data(driver, url, price_extractor)
                
                if pdp_data.get('pdp_scraped'):
                    # Merge data into product
                    product.update(pdp_data)
                    enriched += 1
                    success = True
                    print(f"   ✅ Enriched successfully")
                    
                    # Show what we got
                    if pdp_data.get('ingredienti'):
                        print(f"      Ingredienti: {pdp_data['ingredienti'][:60]}...")
                    if pdp_data.get('tecnologie'):
                        print(f"      Tecnologie: {pdp_data['tecnologie']}")
                    
                    # ⭐ SHOW PRICES
                    if pdp_data.get('regular_price'):
                        print(f"      💰 Regular: €{pdp_data['regular_price']:.2f}")
                    if pdp_data.get('promo_price'):
                        print(f"      🎁 Promo: €{pdp_data['promo_price']:.2f} (-{pdp_data.get('discount_percent', 0)}%)")
                else:
                    errors += 1
                    print(f"   ⚠️  Scraping failed")
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                if attempt == MAX_RETRIES:
                    errors += 1
                    product['pdp_scraped'] = False
                    product['pdp_error'] = str(e)
            
            # Delay between requests (be nice!)
            if idx < total:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Progress summary every 50 products
        if idx % 50 == 0:
            print("\n" + "=" * 70)
            print(f"📊 PROGRESS CHECKPOINT:")
            print(f"   Processed: {idx}/{total} ({idx/total*100:.1f}%)")
            print(f"   Enriched: {enriched}")
            print(f"   Errors: {errors}")
            print(f"   Success rate: {enriched/idx*100:.1f}%")
            print(f"   Time elapsed: {elapsed/60:.1f} minutes")
            print("=" * 70)
    
    return enriched, errors

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 70)
    print("GLAMHAIRSHOP - PDP ENRICHMENT (WITH PRICES)")
    print("=" * 70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print("-" * 70)
    
    # Load products
    print(f"\n📂 Loading products...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"✅ Loaded {len(products)} products")
    
    # Backup original
    print(f"\n💾 Creating backup...")
    import shutil
    shutil.copy(INPUT_FILE, BACKUP_FILE)
    print(f"✅ Backup saved: {BACKUP_FILE.name}")
    
    # Setup driver
    print(f"\n🚀 Starting Chrome driver...")
    driver = setup_driver()
    print(f"✅ Driver ready")
    
    try:
        # Scrape all PDPs
        enriched, errors = scrape_all_pdps(products, driver)
        
        # Save enriched data
        print(f"\n💾 Saving enriched data...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        print(f"✅ Saved: {OUTPUT_FILE.name} ({file_size:.1f} MB)")
        
        # Final summary
        print("\n" + "=" * 70)
        print("PDP ENRICHMENT COMPLETED!")
        print("=" * 70)
        
        print(f"\n📊 FINAL STATS:")
        print(f"   Total products: {len(products)}")
        print(f"   Successfully enriched: {enriched} ({enriched/len(products)*100:.1f}%)")
        print(f"   Errors: {errors} ({errors/len(products)*100:.1f}%)")
        
        print(f"\n📁 FILES:")
        print(f"   Original (backup): {BACKUP_FILE.name}")
        print(f"   Enriched: {OUTPUT_FILE.name}")
        
        print(f"\n✅ Ready for embeddings generation!")
        print("=" * 70)
        
    finally:
        driver.quit()
        print("\n🔒 Driver closed")

if __name__ == '__main__':
    main()
