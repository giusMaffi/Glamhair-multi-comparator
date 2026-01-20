#!/usr/bin/env python3
"""
GLAMHAIRSHOP - Parrucchiere Scraper
====================================
Purpose: Scrape all 293 products from /prodotti-per-parrucchieri
Author: Peppe
Date: 2026-01-20

Strategy:
- Use Selenium (JavaScript rendering)
- Scroll + Load More until all products loaded
- Extract from PrestaShop structure
- Save to JSON

URL: https://www.glamhairshop.it/prodotti-per-parrucchieri
Expected: 293 products
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# ============================================
# CONFIGURATION
# ============================================
TARGET_URL = "https://www.glamhairshop.it/prodotti-per-parrucchieri"
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'products'
OUTPUT_FILE = OUTPUT_DIR / 'parrucchiere_products.json'

# PrestaShop selectors (verified from page)
SELECTORS = {
    'product_container': 'article.product-miniature',
    'product_link': 'h3.product-title a, h2.product-title a',
    'product_name': 'h3.product-title a, h2.product-title a',
    'product_price': '.product-price-and-shipping .price',
    'product_image': '.thumbnail-container img',
    'load_more_button': 'button.loadMore, a.loadMore, .js-product-list-pagination a',
}

# ============================================
# SELENIUM SETUP
# ============================================
def setup_driver():
    """Setup Chrome driver with headless options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

# ============================================
# SCROLL & LOAD MORE
# ============================================
def load_all_products(driver, max_attempts=30):
    """
    Scroll page and click 'Load More' until all products visible
    
    Args:
        driver: Selenium WebDriver
        max_attempts: Max number of load more clicks
    
    Returns:
        int: Total products loaded
    """
    print("⏳ Loading all products...")
    
    previous_count = 0
    attempts = 0
    no_change_count = 0
    
    while attempts < max_attempts:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        
        # Count current products
        products = driver.find_elements(By.CSS_SELECTOR, SELECTORS['product_container'])
        current_count = len(products)
        
        print(f"  📦 Loaded: {current_count} products (attempt {attempts + 1}/{max_attempts})")
        
        # Check if count changed
        if current_count == previous_count:
            no_change_count += 1
            if no_change_count >= 3:
                print(f"  ✅ No new products after 3 attempts. Total: {current_count}")
                break
        else:
            no_change_count = 0
        
        previous_count = current_count
        
        # Try to find and click "Load More" button
        try:
            # Try multiple possible selectors
            load_more = None
            for selector in ['button.loadMore', 'a.loadMore', '.js-product-list-pagination a']:
                try:
                    load_more = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if load_more:
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", load_more)
                print(f"  🔘 Clicked 'Load More'")
                time.sleep(2)
            else:
                print(f"  ℹ️  No 'Load More' button found")
                # Try scrolling more anyway
                for _ in range(3):
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(0.3)
        
        except TimeoutException:
            print(f"  ℹ️  No more 'Load More' button")
        except Exception as e:
            print(f"  ⚠️  Error clicking Load More: {e}")
        
        attempts += 1
    
    final_count = len(driver.find_elements(By.CSS_SELECTOR, SELECTORS['product_container']))
    print(f"\n✅ Final product count: {final_count}")
    return final_count

# ============================================
# EXTRACT PRODUCTS
# ============================================
def extract_products(driver):
    """
    Extract product data from loaded page
    
    Returns:
        list: List of product dictionaries
    """
    print("\n🔍 Extracting product data...")
    
    # Get page HTML
    from bs4 import BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    
    # Find all product containers
    containers = soup.select(SELECTORS['product_container'])
    print(f"  📦 Found {len(containers)} product containers")
    
    products = []
    seen_urls = set()
    
    for idx, container in enumerate(containers, 1):
        try:
            # Product name & URL
            name_elem = container.select_one(SELECTORS['product_name'])
            if not name_elem:
                print(f"  ⚠️  Product {idx}: No name element")
                continue
            
            name = name_elem.get_text(strip=True)
            url = name_elem.get('href', '')
            
            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Price
            price_elem = container.select_one(SELECTORS['product_price'])
            price = ''
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Clean price: "99,00 €" -> "99.00"
                price = price_text.replace('€', '').replace(',', '.').strip()
            
            # Image
            img_elem = container.select_one(SELECTORS['product_image'])
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # Category (from breadcrumb or page context)
            category = 'Parrucchiere'
            
            # Brand (try to extract from name or other elements)
            brand = extract_brand_from_name(name)
            
            # Build product object
            product = {
                'id': f"GLAM_PARR_{len(products) + 1:03d}",
                'nome': name,
                'brand': brand,
                'categoria': category,
                'subcategoria': '',  # Could extract from filters/breadcrumb
                'prezzo': price,
                'url': url,
                'immagine': image_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            products.append(product)
            
            if (idx) % 50 == 0:
                print(f"  ✅ Extracted {idx}/{len(containers)} products")
        
        except Exception as e:
            print(f"  ❌ Error extracting product {idx}: {e}")
            continue
    
    print(f"\n✅ Extracted {len(products)} unique products")
    return products

# ============================================
# HELPER FUNCTIONS
# ============================================
def extract_brand_from_name(name):
    """
    Try to extract brand from product name
    
    Common brands in Parrucchiere:
    - GHD, Parlux, Corioliss, Wella, L'Oreal, etc.
    """
    name_lower = name.lower()
    
    brands = [
        'ghd', 'parlux', 'corioliss', 'babyliss', 'wella', 
        'l\'oreal', 'loreal', 'schwarzkopf', 'goldwell',
        'matrix', 'redken', 'kerastase', 'alfaparf',
        'remington', 'imetec', 'max pro', 'moser'
    ]
    
    for brand in brands:
        if brand in name_lower:
            return brand.upper()
    
    # Default
    return 'Parrucchiere'

# ============================================
# SAVE TO JSON
# ============================================
def save_products(products, filepath):
    """Save products to JSON file"""
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(products)} products to: {filepath}")
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"  Total products: {len(products)}")
    print(f"  File size: {filepath.stat().st_size / 1024:.1f} KB")
    
    # Brand distribution
    brands = {}
    for p in products:
        brand = p['brand']
        brands[brand] = brands.get(brand, 0) + 1
    
    print(f"\n  Brand distribution:")
    for brand, count in sorted(brands.items(), key=lambda x: -x[1])[:10]:
        print(f"    {brand}: {count}")

# ============================================
# MAIN
# ============================================
def main():
    """Main scraping function"""
    print("=" * 70)
    print("GLAMHAIRSHOP - PARRUCCHIERE SCRAPER")
    print("=" * 70)
    print(f"\nTarget URL: {TARGET_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"\nStarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    driver = None
    
    try:
        # 1. Setup driver
        print("\n🚀 Setting up Chrome driver...")
        driver = setup_driver()
        
        # 2. Load page
        print(f"\n🌐 Loading page: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # Wait for products to appear
        print("⏳ Waiting for products to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['product_container']))
        )
        print("✅ Products container found")
        
        # 3. Load all products
        total_loaded = load_all_products(driver, max_attempts=30)
        
        # 4. Extract data
        products = extract_products(driver)
        
        # 5. Save to JSON
        save_products(products, OUTPUT_FILE)
        
        print("\n" + "=" * 70)
        print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print("\n🔚 Driver closed")

if __name__ == '__main__':
    main()