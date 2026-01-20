#!/usr/bin/env python3
"""
GLAMHAIRSHOP - Universal Scraper FIXED
=======================================
Purpose: Re-scrape Skincare + Esigenze with increased max_attempts
Author: Peppe
Date: 2026-01-20

FIX:
- max_attempts: 40 → 150 (for large categories)
- Better Load More detection
- Only scrape: skincare (767) + esigenze (1977)

Expected results:
- Skincare: 767 products (was 492)
- Esigenze: 1977 products (was 492)
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ============================================
# CONFIGURATION
# ============================================

# Categories to RE-SCRAPE (only problematic ones)
CATEGORIES = [
    {
        "name": "skincare",
        "url": "https://www.glamhairshop.it/skin-care",
        "expected_count": 767,
        "priority": 1
    },
    {
        "name": "esigenze",
        "url": "https://www.glamhairshop.it/esigenze",
        "expected_count": 1977,
        "priority": 2
    }
]

# Output configuration
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'products'

# PrestaShop selectors
SELECTORS = {
    'product_container': 'article.product-miniature',
    'product_link': 'h3.product-title a, h2.product-title a',
    'product_name': 'h3.product-title a, h2.product-title a',
    'product_price': '.product-price-and-shipping .price',
    'product_image': '.thumbnail-container img',
    'load_more_button': 'button.loadMore, a.loadMore, .js-product-list-pagination a',
}

# Brand extraction patterns
KNOWN_BRANDS = [
    # Haircare
    'kerastase', 'olaplex', 'davines', 'aveda', 'redken', 'wella', 
    'schwarzkopf', 'matrix', 'goldwell', 'joico', 'moroccanoil',
    # Skincare
    'collistar', 'rilastil', 'bioderma', 'la roche posay', 'vichy',
    'eucerin', 'neutrogena', 'garnier', 'nivea', 'l\'oreal',
    # Makeup
    'maybelline', 'nyx', 'catrice', 'essence', 'rimmel',
    # Profumi
    'dior', 'chanel', 'armani', 'versace', 'paco rabanne',
    # Professional
    'ghd', 'parlux', 'babyliss', 'remington', 'corioliss',
    'alfaparf', 'lisap', 'framesi', 'inebrya', 'selective',
    # Others
    'pantene', 'head & shoulders', 'dove', 'tresemme'
]

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
# SCRAPING LOGIC - IMPROVED
# ============================================
def load_all_products(driver, category_name, expected_count, max_attempts=150):
    """
    FIXED VERSION: More aggressive loading
    
    Args:
        driver: Selenium WebDriver
        category_name: Name of category
        expected_count: Expected number of products
        max_attempts: Max Load More clicks (INCREASED to 150)
    
    Returns:
        int: Total products loaded
    """
    print(f"⏳ Loading products (target: {expected_count})...")
    
    previous_count = 0
    attempts = 0
    no_change_count = 0
    last_report = 0
    
    while attempts < max_attempts:
        # Scroll to bottom aggressively
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)  # Slightly faster
        
        # Count products
        products = driver.find_elements(By.CSS_SELECTOR, SELECTORS['product_container'])
        current_count = len(products)
        
        # Progress reporting every 10 attempts
        if attempts % 10 == 0 or current_count != last_report:
            progress = (current_count / expected_count * 100) if expected_count > 0 else 0
            print(f"  📦 Progress: {current_count}/{expected_count} ({progress:.1f}%) - Attempt {attempts + 1}")
            last_report = current_count
        
        # Check if we reached target
        if current_count >= expected_count:
            print(f"  ✅ Target reached! {current_count} products loaded")
            break
        
        # Check if count changed
        if current_count == previous_count:
            no_change_count += 1
            # Only stop if no change for 5 attempts (increased from 3)
            if no_change_count >= 5:
                print(f"  ⚠️  No new products after 5 attempts. Stopping at {current_count}")
                break
        else:
            no_change_count = 0
        
        previous_count = current_count
        
        # Try to find and click "Load More" - TRY HARDER
        load_more_clicked = False
        
        # Try multiple selectors
        for selector in ['button.loadMore', 'a.loadMore', '.js-product-list-pagination a', 
                         'button[type="button"]', '.btn-load-more', '.load-more']:
            try:
                load_more = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more)
                time.sleep(0.3)
                
                # Click with JavaScript (more reliable)
                driver.execute_script("arguments[0].click();", load_more)
                
                load_more_clicked = True
                time.sleep(1.5)  # Wait for new products to load
                break
                
            except:
                continue
        
        if not load_more_clicked:
            # If no button found, scroll more aggressively
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.2)
        
        attempts += 1
    
    final_count = len(driver.find_elements(By.CSS_SELECTOR, SELECTORS['product_container']))
    
    accuracy = (final_count / expected_count * 100) if expected_count > 0 else 0
    print(f"\n✅ Final count: {final_count}/{expected_count} ({accuracy:.1f}%)")
    
    return final_count

def extract_brand_from_name(name: str) -> str:
    """Extract brand from product name"""
    name_lower = name.lower()
    
    for brand in KNOWN_BRANDS:
        if brand in name_lower:
            if "'" in brand:
                return brand.title()
            return brand.upper()
    
    return 'Unknown'

def extract_products(driver, category_name: str) -> List[Dict]:
    """Extract product data from loaded page"""
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    
    containers = soup.select(SELECTORS['product_container'])
    print(f"\n🔍 Extracting data from {len(containers)} product containers...")
    
    products = []
    seen_urls = set()
    
    for idx, container in enumerate(containers, 1):
        try:
            # Name & URL
            name_elem = container.select_one(SELECTORS['product_name'])
            if not name_elem:
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
                price = price_text.replace('€', '').replace(',', '.').strip()
            
            # Image
            img_elem = container.select_one(SELECTORS['product_image'])
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # Brand
            brand = extract_brand_from_name(name)
            
            # Build product
            product = {
                'id': f"GLAM_{category_name.upper()}_{len(products) + 1:04d}",
                'nome': name,
                'brand': brand,
                'categoria': category_name,
                'subcategoria': '',
                'prezzo': price,
                'url': url,
                'immagine': image_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            products.append(product)
            
            # Progress every 100 products
            if len(products) % 100 == 0:
                print(f"  ✅ Extracted {len(products)} unique products...")
        
        except Exception as e:
            continue
    
    print(f"\n✅ Total extracted: {len(products)} unique products")
    return products

# ============================================
# CATEGORY SCRAPING
# ============================================
def scrape_category(category: Dict, driver) -> Dict:
    """Scrape single category with FIXED logic"""
    print(f"\n{'='*70}")
    print(f"RE-SCRAPING: {category['name'].upper()}")
    print(f"{'='*70}")
    print(f"URL: {category['url']}")
    print(f"Target: {category['expected_count']} products")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 70)
    
    try:
        # Load page
        driver.get(category['url'])
        
        # Wait for products
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['product_container']))
        )
        
        # Load all products with INCREASED max_attempts
        total_loaded = load_all_products(
            driver, 
            category['name'], 
            category['expected_count'],
            max_attempts=150  # INCREASED!
        )
        
        # Extract data
        products = extract_products(driver, category['name'])
        
        # Stats
        accuracy = (len(products) / category['expected_count'] * 100) if category['expected_count'] > 0 else 0
        
        result = {
            'category': category['name'],
            'url': category['url'],
            'expected': category['expected_count'],
            'scraped': len(products),
            'accuracy': f"{accuracy:.1f}%",
            'products': products,
            'success': True,
            'completed_at': datetime.now().isoformat()
        }
        
        print(f"\n✅ SUCCESS!")
        print(f"   Scraped: {len(products)}/{category['expected_count']}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        return result
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'category': category['name'],
            'url': category['url'],
            'expected': category['expected_count'],
            'scraped': 0,
            'accuracy': '0%',
            'products': [],
            'success': False,
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

# ============================================
# SAVE RESULTS
# ============================================
def save_results(results: List[Dict]):
    """Save category files (OVERWRITE previous partial results)"""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result['success'] and result['products']:
            filepath = OUTPUT_DIR / f"{result['category']}_products.json"
            
            # Backup old file if exists
            if filepath.exists():
                backup = OUTPUT_DIR / f"{result['category']}_products_OLD.json"
                import shutil
                shutil.copy(filepath, backup)
                print(f"📦 Backed up old file to: {backup.name}")
            
            # Save new file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result['products'], f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved: {filepath.name} ({len(result['products'])} products)")

# ============================================
# MAIN
# ============================================
def main():
    """Main re-scraping function"""
    print("=" * 70)
    print("GLAMHAIRSHOP - FIXED RE-SCRAPER")
    print("=" * 70)
    print(f"\nRe-scraping: Skincare + Esigenze")
    print(f"max_attempts: 150 (was 40)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    driver = None
    results = []
    
    try:
        # Setup
        print("\n🚀 Setting up Chrome driver...")
        driver = setup_driver()
        
        # Scrape each category
        for idx, category in enumerate(CATEGORIES, 1):
            print(f"\n\n[{idx}/{len(CATEGORIES)}] Processing: {category['name']}")
            result = scrape_category(category, driver)
            results.append(result)
            
            # Delay between categories
            if idx < len(CATEGORIES):
                print("\n⏸️  Waiting 5 seconds...")
                time.sleep(5)
        
        # Save
        save_results(results)
        
        # Final report
        print("\n" + "=" * 70)
        print("RE-SCRAPING COMPLETED!")
        print("=" * 70)
        
        total_scraped = sum(r['scraped'] for r in results if r['success'])
        total_expected = sum(r['expected'] for r in results)
        
        print(f"\nRESULTS:")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['category']:12} → {result['scraped']:4}/{result['expected']:4} ({result['accuracy']})")
        
        print(f"\nTOTAL: {total_scraped}/{total_expected}")
        
        overall_accuracy = (total_scraped / total_expected * 100) if total_expected > 0 else 0
        print(f"Overall accuracy: {overall_accuracy:.1f}%")
        
        print("\n" + "=" * 70)
    
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