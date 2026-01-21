#!/usr/bin/env python3
"""
PDP Extraction Test - WITH PRICES
==================================
Purpose: Test price extraction on sample products before full scraping
Author: Peppe
Date: 2026-01-20

Tests extraction on 3 representative products:
1. Kerastase Chronologiste (Haircare Premium)
2. Macadamia Smoothing Shampoo (Haircare)
3. Tisanoreica Integratore (Supplements)

Verifies extraction of:
- Descrizione
- Ingredienti
- Modo d'uso
- Tecnologie
- **PRICES** (regular, promo, discount)
"""

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ============================================
# PRICE EXTRACTOR (same as main script)
# ============================================

class PriceExtractor:
    """Extract prices from product HTML pages"""
    
    def __init__(self):
        self.price_pattern = re.compile(r'(\d+[,\.]\d{2})\s*€')
        self.price_selectors = {
            'regular': ['.regular-price', '.old-price', '.product-price .regular-price', 'span.regular-price'],
            'current': ['.price:not(.regular-price)', '.product-price .price', '.current-price', 'span.price'],
            'discount': ['.discount', '.discount-percentage', 'span.discount']
        }
    
    def extract_prices(self, soup: BeautifulSoup):
        result = {'regular_price': None, 'promo_price': None, 'discount_percent': None}
        
        # Try selectors first
        prices = self._extract_with_selectors(soup)
        if prices['regular_price'] or prices['promo_price']:
            return prices
        
        # Fallback to patterns
        return self._extract_with_patterns(soup)
    
    def _extract_with_selectors(self, soup: BeautifulSoup):
        result = {'regular_price': None, 'promo_price': None, 'discount_percent': None}
        
        for selector in self.price_selectors['regular']:
            elem = soup.select_one(selector)
            if elem:
                price = self._parse_price(elem.get_text(strip=True))
                if price:
                    result['regular_price'] = price
                    break
        
        for selector in self.price_selectors['current']:
            elem = soup.select_one(selector)
            if elem:
                price = self._parse_price(elem.get_text(strip=True))
                if price:
                    result['promo_price'] = price
                    break
        
        for selector in self.price_selectors['discount']:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                discount = self._parse_discount(text)
                if discount:
                    result['discount_percent'] = discount
                    break
        
        if result['promo_price'] and not result['regular_price']:
            if not result['discount_percent']:
                result['regular_price'] = result['promo_price']
                result['promo_price'] = None
        
        return result
    
    def _extract_with_patterns(self, soup: BeautifulSoup):
        result = {'regular_price': None, 'promo_price': None, 'discount_percent': None}
        page_text = soup.get_text()
        price_matches = self.price_pattern.findall(page_text)
        
        if len(price_matches) >= 2:
            result['regular_price'] = self._parse_price(price_matches[0])
            result['promo_price'] = self._parse_price(price_matches[1])
        elif len(price_matches) == 1:
            result['regular_price'] = self._parse_price(price_matches[0])
        
        discount_pattern = re.compile(r'-\s*(\d+)\s*%')
        discount_match = discount_pattern.search(page_text)
        if discount_match:
            result['discount_percent'] = int(discount_match.group(1))
        
        return result
    
    def _parse_price(self, price_text: str):
        if not price_text:
            return None
        clean_text = price_text.replace('€', '').strip().replace(',', '.')
        try:
            return float(clean_text)
        except (ValueError, AttributeError):
            return None
    
    def _parse_discount(self, discount_text: str):
        if not discount_text:
            return None
        pattern = re.compile(r'(\d+)\s*%')
        match = pattern.search(discount_text)
        return int(match.group(1)) if match else None

# ============================================
# TEST URLS
# ============================================

TEST_PRODUCTS = [
    {
        'name': 'Kerastase Chronologiste (Haircare Premium)',
        'url': 'https://www.glamhairshop.it/chronologiste/kerastase-chronologiste-bain-regenerant-250-ml'
    },
    {
        'name': 'Macadamia Smoothing Shampoo (Haircare)',
        'url': 'https://www.glamhairshop.it/macadamia/macadamia-smoothing-shampoo-1000-ml'
    },
    {
        'name': 'Tisanoreica Integratore (Supplements)',
        'url': 'https://www.glamhairshop.it/gianluca-mech-tisanoreica/tisanoreica-decottopia-estratto-21-snel-uomo-500ml'
    }
]

# ============================================
# EXTRACTION FUNCTIONS
# ============================================

def extract_description_tab(soup: BeautifulSoup):
    result = {'descrizione_completa': '', 'ingredienti': '', 'modo_uso': '', 'tecnologie': ''}
    
    desc_selectors = ['#description', 'div[id="description"]', '.product-description', '[itemprop="description"]']
    description_div = None
    for selector in desc_selectors:
        description_div = soup.select_one(selector)
        if description_div:
            break
    
    if not description_div:
        return result
    
    full_text = description_div.get_text(separator=' ', strip=True)
    result['descrizione_completa'] = full_text
    
    text_lower = full_text.lower()
    
    # Ingredienti
    ingredienti_patterns = [
        r'ingredienti[:\s]+([^\.]+)', r'inci[:\s]+([^\.]+)',
        r'formulato con[:\s]+([^\.]+)', r'contiene[:\s]+([^\.]+)'
    ]
    for pattern in ingredienti_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            result['ingredienti'] = match.group(1).strip()
            break
    
    # Modo d'uso
    uso_patterns = [
        r'(?:applicazione|modo d.uso|come usare|utilizzo)[:\s]+([^\.]+(?:\.[^\.]+){0,2})'
    ]
    for pattern in uso_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            result['modo_uso'] = match.group(1).strip()
            break
    
    # Tecnologie
    tech_keywords = [
        'abissina', 'acido ialuronico', 'vitamina e', 'keratina',
        'olio di macadamia', 'caviale', 'omega 3', 'omega 5', 'omega 7'
    ]
    found_tech = [tech.title() for tech in tech_keywords if tech in text_lower]
    result['tecnologie'] = ', '.join(found_tech) if found_tech else ''
    
    return result

# ============================================
# TEST EXECUTION
# ============================================

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
    return webdriver.Chrome(options=chrome_options)

def test_extraction():
    print("=" * 70)
    print("PDP EXTRACTION TEST - WITH PRICES")
    print("=" * 70)
    
    driver = setup_driver()
    price_extractor = PriceExtractor()
    
    try:
        for i, product in enumerate(TEST_PRODUCTS, 1):
            print(f"\n{'=' * 70}")
            print(f"🧪 TESTING: {product['name']}")
            print(f"URL: {product['url']}")
            print("=" * 70)
            
            driver.get(product['url'])
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract data
            desc_data = extract_description_tab(soup)
            price_data = price_extractor.extract_prices(soup)
            
            # Display results
            print(f"\n📊 EXTRACTED DATA:")
            
            print(f"\n1️⃣  DESCRIZIONE COMPLETA:")
            if desc_data['descrizione_completa']:
                preview = desc_data['descrizione_completa'][:200]
                print(f"   Length: {len(desc_data['descrizione_completa'])} chars")
                print(f"   Preview: {preview}...")
            else:
                print(f"   ❌ NOT FOUND")
            
            print(f"\n2️⃣  INGREDIENTI:")
            print(f"   {desc_data['ingredienti'] if desc_data['ingredienti'] else '❌ NOT FOUND'}")
            
            print(f"\n3️⃣  MODO D'USO:")
            print(f"   {desc_data['modo_uso'] if desc_data['modo_uso'] else '❌ NOT FOUND'}")
            
            print(f"\n4️⃣  TECNOLOGIE:")
            print(f"   {desc_data['tecnologie'] if desc_data['tecnologie'] else '❌ NOT FOUND'}")
            
            print(f"\n5️⃣  💰 PREZZI (NEW!):")
            if price_data['regular_price']:
                print(f"   Regular Price: €{price_data['regular_price']:.2f}")
            else:
                print(f"   Regular Price: ❌ NOT FOUND")
            
            if price_data['promo_price']:
                print(f"   Promo Price: €{price_data['promo_price']:.2f}")
                if price_data['discount_percent']:
                    print(f"   Discount: {price_data['discount_percent']}%")
                    savings = price_data['regular_price'] - price_data['promo_price']
                    print(f"   You Save: €{savings:.2f}")
            else:
                print(f"   Promo Price: N/A (no discount)")
        
        # Summary
        print(f"\n{'=' * 70}")
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"\n{product['name']}:")
        for key in ['descrizione_completa', 'ingredienti', 'modo_uso', 'tecnologie']:
            status = "✅" if desc_data.get(key) else "❌"
            length = f"({len(desc_data.get(key, ''))} chars)" if desc_data.get(key) else ""
            print(f"  {key.title()}: {status} {length}")
        
        # Price summary
        print(f"\n💰 PRICE DATA:")
        price_status = "✅" if price_data['regular_price'] else "❌"
        promo_status = "✅" if price_data['promo_price'] else "N/A"
        print(f"  Regular Price: {price_status}")
        print(f"  Promo Price: {promo_status}")
        
        print(f"\n{'=' * 70}")
        print("✅ Test completato!")
        print("=" * 70)
        
    finally:
        driver.quit()

if __name__ == '__main__':
    test_extraction()
