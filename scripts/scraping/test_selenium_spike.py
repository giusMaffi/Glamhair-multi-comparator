#!/usr/bin/env python3
"""
GLAMHAIRSHOP - Selenium Test Spike
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'raw'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / 'test_olaplex_selenium.json'

def run_selenium_test():
    print("=" * 60)
    print("🚀 GLAMHAIRSHOP - Selenium Test")
    print("=" * 60)
    
    print("🔧 Setting up Chrome...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        print("📡 Loading page...")
        driver.get('https://www.glamhairshop.it/olaplex')
        
        print("⏳ Waiting for products...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.product-miniature"))
        )
        print("✅ Page loaded!")
        
        # Scroll to button
        print("📜 Scrolling to bottom...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Click "CARICA DI PIÙ" button
        print("🔘 Looking for 'CARICA DI PIÙ' button...")
        try:
            load_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.loadMore"))
            )
            print("✅ Found button, clicking...")
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(3)
            print("✅ Clicked! Waiting for new products...")
        except Exception as e:
            print(f"⚠️  Button not found or not clickable: {e}")
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        containers = soup.select('article.product-miniature')
        print(f"🔍 Found {len(containers)} product containers")
        
        products = []
        seen_urls = set()
        
        for idx, container in enumerate(containers, 1):
            try:
                name_elem = container.select_one('h3.product-title a, h2.product-title a')
                price_elem = container.select_one('.product-price-and-shipping .price')
                
                if name_elem and price_elem:
                    url = name_elem.get('href', '')
                    
                    if url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    
                    product = {
                        'id': f"GLAM_{idx:03d}",
                        'nome': name_elem.get_text(strip=True),
                        'prezzo': price_elem.get_text(strip=True),
                        'url': url
                    }
                    products.append(product)
                    
            except Exception as e:
                continue
        
        print(f"✅ Extracted {len(products)} unique products")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to: {OUTPUT_FILE}")
        
        print("\n📦 SAMPLE PRODUCTS:")
        for i, p in enumerate(products[:5], 1):
            print(f"\n{i}. {p['nome']}")
            print(f"   Prezzo: {p['prezzo']}")
            print(f"   URL: {p['url'][:60]}...")
        
        print(f"\n🎯 Total unique products: {len(products)}")
        print("=" * 60)
        print("✅ TEST COMPLETED!")
        print("=" * 60)
        
    finally:
        driver.quit()

if __name__ == '__main__':
    run_selenium_test()