#!/usr/bin/env python3
"""
GLAMHAIRSHOP - Production Scraper (FULL CATALOG)
=================================================
Scrapes ENTIRE catalog from glamhairshop.it
Auto-discovers all brands and categories
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
from typing import List, Dict, Set
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data' / 'products'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Output files
HAIRCARE_OUTPUT = DATA_DIR / 'haircare_products.json'
PARRUCCHIERE_OUTPUT = DATA_DIR / 'parrucchiere_products.json'
CHECKPOINT_FILE = BASE_DIR / 'data' / 'raw' / 'scraper_checkpoint.json'

# Configuration
BASE_URL = "https://www.glamhairshop.it"
RATE_LIMIT_DELAY = 2  # seconds between requests


class GlamhairshopScraper:
    """Production scraper for entire Glamhairshop catalog"""
    
    def __init__(self):
        self.driver = None
        self.products = []
        self.stats = {
            'total_products': 0,
            'total_pages': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
    def setup_driver(self):
        """Initialize Chrome driver"""
        logger.info("🔧 Setting up Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logger.info("✅ Chrome driver ready")
        
    def discover_haircare_brands(self) -> List[str]:
        """Auto-discover all hair care brand URLs"""
        logger.info("\n🔍 Discovering Hair Care brands...")
        
        try:
            self.driver.get(f"{BASE_URL}/hair-care")
            time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all brand links
            brand_links = set()
            
            # Strategy 1: Look for brand links in sidebar/filters
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # Filter for brand pages (typical patterns)
                if any(brand in href.lower() for brand in [
                    'olaplex', 'kerastase', 'aveda', 'davines', 'redken',
                    'alfaparf', 'loreal', 'shu-uemura', 'oribe', 'moroccanoil',
                    'tigi', 'matrix', 'wella', 'revlon', 'framesi', 'kemon',
                    'ghd', 'parlux', 'yellow', 'lisap', 'medavita'
                ]):
                    # Extract clean brand slug
                    if href.startswith('/'):
                        brand_slug = href.strip('/').split('/')[0]
                        if brand_slug and brand_slug != 'hair-care':
                            brand_links.add(brand_slug)
                    elif BASE_URL in href:
                        brand_slug = href.replace(BASE_URL, '').strip('/').split('/')[0]
                        if brand_slug and brand_slug != 'hair-care':
                            brand_links.add(brand_slug)
            
            brands = sorted(list(brand_links))
            logger.info(f"✅ Found {len(brands)} brands")
            
            # Log brands found
            for brand in brands:
                logger.info(f"   • {brand}")
                
            return brands
            
        except Exception as e:
            logger.error(f"❌ Error discovering brands: {e}")
            # Fallback to known brands
            return self._fallback_brands()
            
    def _fallback_brands(self) -> List[str]:
        """Fallback list of known brands"""
        return [
            'olaplex', 'kerastase', 'aveda', 'davines', 'redken',
            'alfaparf-milano', 'loreal-professionnel', 'shu-uemura',
            'oribe', 'moroccanoil', 'ghd', 'parlux', 'tigi-bed-head',
            'matrix', 'wella-sp', 'revlon-professional', 'framesi',
            'kemon', 'yellow-professional', 'lisap-milano', 'medavita',
            'macadamia', 'nanokeratin', 'american-crew'
        ]
        
    def scrape_page(self, url_or_slug: str, category: str = 'haircare') -> List[Dict]:
        """Scrape all products from a page"""
        
        # Build full URL
        if url_or_slug.startswith('http'):
            url = url_or_slug
            slug = url_or_slug.split('/')[-1]
        else:
            url = f"{BASE_URL}/{url_or_slug}"
            slug = url_or_slug
            
        logger.info(f"📡 Scraping: {slug}")
        
        try:
            self.driver.get(url)
            
            # Wait for products
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.product-miniature"))
            )
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Click "Carica di più" if exists
            self._click_load_more()
            
            # Extract products
            products = self._extract_products_from_page(slug, category)
            
            logger.info(f"   ✅ {len(products)} products")
            self.stats['total_pages'] += 1
            
            return products
            
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            self.stats['errors'] += 1
            return []
            
    def _click_load_more(self):
        """Click 'Carica di più' button if present"""
        try:
            load_more = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.loadMore"))
            )
            self.driver.execute_script("arguments[0].click();", load_more)
            time.sleep(3)
            logger.info("   🔘 Loaded more products")
        except:
            pass
            
    def _extract_products_from_page(self, brand: str, category: str) -> List[Dict]:
        """Extract product data from current page"""
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        containers = soup.select('article.product-miniature')
        products = []
        seen_urls = set()
        
        for container in containers:
            try:
                name_elem = container.select_one('h3.product-title a, h2.product-title a')
                price_elem = container.select_one('.product-price-and-shipping .price')
                
                if not name_elem or not price_elem:
                    continue
                    
                url = name_elem.get('href', '')
                
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Parse price
                price_text = price_elem.get_text(strip=True)
                price_clean = price_text.replace('€', '').replace(',', '.').strip()
                
                # Original price
                original_price = None
                original_elem = container.select_one('.regular-price')
                if original_elem:
                    original_text = original_elem.get_text(strip=True)
                    original_price = original_text.replace('€', '').replace(',', '.').strip()
                
                # Image
                image_url = None
                img_elem = container.select_one('.product-thumbnail img')
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src')
                
                product = {
                    'id': self._generate_id(url),
                    'nome': name_elem.get_text(strip=True),
                    'brand': brand.replace('-', ' ').title(),
                    'categoria': category,
                    'prezzo': price_clean,
                    'prezzo_originale': original_price,
                    'url': url,
                    'immagine': image_url,
                    'scraped_at': datetime.now().isoformat()
                }
                
                products.append(product)
                
            except Exception as e:
                continue
                
        return products
        
    def _generate_id(self, url: str) -> str:
        """Generate product ID from URL"""
        parts = url.rstrip('/').split('/')
        slug = parts[-1] if parts else 'unknown'
        return f"GLAM_{slug.upper().replace('-', '_')}"
        
    def scrape_all_haircare(self) -> List[Dict]:
        """Scrape ALL hair care brands"""
        logger.info("=" * 60)
        logger.info("🚀 SCRAPING ALL HAIR CARE BRANDS")
        logger.info("=" * 60)
        
        # Discover brands
        brands = self.discover_haircare_brands()
        
        all_products = []
        
        for idx, brand in enumerate(brands, 1):
            logger.info(f"\n[{idx}/{len(brands)}] {brand}")
            
            products = self.scrape_page(brand, 'haircare')
            all_products.extend(products)
            
            # Rate limiting
            if idx < len(brands):
                time.sleep(RATE_LIMIT_DELAY)
                
        logger.info(f"\n✅ Hair Care Complete: {len(all_products)} products from {len(brands)} brands")
        return all_products
        
    def scrape_all_parrucchiere(self) -> List[Dict]:
        """Scrape parrucchiere category"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 SCRAPING PARRUCCHIERE")
        logger.info("=" * 60)
        
        products = self.scrape_page('parrucchiere', 'parrucchiere')
        
        logger.info(f"\n✅ Parrucchiere Complete: {len(products)} products")
        return products
        
    def save_products(self, products: List[Dict], output_file: Path):
        """Save products to JSON file"""
        logger.info(f"\n💾 Saving {len(products)} products to {output_file.name}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Saved!")
        
    def generate_report(self, haircare_count: int, parrucchiere_count: int):
        """Generate scraping report"""
        duration = datetime.now() - self.stats['start_time']
        
        report = [
            "\n" + "=" * 60,
            "📊 SCRAPING REPORT",
            "=" * 60,
            f"Hair Care Products: {haircare_count}",
            f"Parrucchiere Products: {parrucchiere_count}",
            f"Total Products: {haircare_count + parrucchiere_count}",
            f"Pages Scraped: {self.stats['total_pages']}",
            f"Errors: {self.stats['errors']}",
            f"Duration: {duration}",
            "=" * 60
        ]
        
        report_text = "\n".join(report)
        logger.info(report_text)
        
        # Save report
        report_file = BASE_DIR / 'data' / 'raw' / 'scraping_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
            
    def run(self):
        """Run complete scraping pipeline"""
        try:
            self.setup_driver()
            
            # Scrape ALL Hair Care
            haircare_products = self.scrape_all_haircare()
            self.save_products(haircare_products, HAIRCARE_OUTPUT)
            
            # Scrape Parrucchiere
            parrucchiere_products = self.scrape_all_parrucchiere()
            self.save_products(parrucchiere_products, PARRUCCHIERE_OUTPUT)
            
            # Report
            self.generate_report(len(haircare_products), len(parrucchiere_products))
            
            logger.info("\n🎉 SCRAPING COMPLETED!")
            
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            raise
            
        finally:
            if self.driver:
                self.driver.quit()


def main():
    scraper = GlamhairshopScraper()
    scraper.run()


if __name__ == '__main__':
    main()