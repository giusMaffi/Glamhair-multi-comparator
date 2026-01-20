#!/usr/bin/env python3
"""
Brand Extraction Fix
====================
Purpose: Fix brand extraction for 1155 "Unknown" products
Author: Peppe
Date: 2026-01-20

Strategy:
- Smart extraction from product name
- First word(s) usually = brand
- Handle multi-word brands
- Proper capitalization
"""

import json
from pathlib import Path
from collections import Counter

# ============================================
# SMART BRAND EXTRACTION
# ============================================

def extract_brand_smart(name: str) -> str:
    """
    Intelligently extract brand from product name
    
    Examples:
    "Kerastase Discipline Bain" → "KERASTASE"
    "La Roche Posay Effaclar" → "LA ROCHE POSAY"
    "Alfaparf Semi di Lino" → "ALFAPARF"
    "L'Oreal Professionnel Serie Expert" → "L'OREAL PROFESSIONNEL"
    """
    
    if not name or not name.strip():
        return 'Unknown'
    
    # Clean name
    name = name.strip()
    words = name.split()
    
    if not words:
        return 'Unknown'
    
    # Start with first word
    brand_parts = [words[0]]
    
    # Multi-word brand detection
    if len(words) >= 2:
        second_word = words[1].lower()
        
        # Common second words in brand names
        second_word_indicators = [
            'roche', 'oreal', 'di', 'della', 'del',
            'prof', 'professionnel', 'professional',
            '&', 'and', 'pour', 'per'
        ]
        
        if second_word in second_word_indicators:
            brand_parts.append(words[1])
            
            # Check for third word
            if len(words) >= 3:
                third_word = words[2].lower()
                
                third_word_indicators = [
                    'posay', 'lino', 'expert', 'hair',
                    'care', 'paris', 'homme', 'uomo'
                ]
                
                if third_word in third_word_indicators:
                    brand_parts.append(words[2])
    
    # Handle L'Oreal special case
    if words[0].lower().startswith("l'"):
        brand_parts = [words[0]]
        if len(words) >= 2 and words[1].lower() in ['professionnel', 'professional', 'paris']:
            brand_parts.append(words[1])
    
    # Join and format
    brand = ' '.join(brand_parts)
    
    # Proper capitalization
    # Exception for L'Oreal
    if brand.lower().startswith("l'"):
        brand = "L'Oreal" if len(brand_parts) == 1 else "L'Oreal " + brand_parts[1].upper()
    else:
        brand = brand.upper()
    
    return brand

# ============================================
# MAIN FIX PROCESS
# ============================================

def main():
    print("=" * 70)
    print("BRAND EXTRACTION FIX")
    print("=" * 70)
    
    # Load data
    input_file = Path('data/products/ALL_PRODUCTS.json')
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"\n📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"✅ Loaded: {len(products)} products")
    
    # Count current Unknown
    unknown_before = sum(1 for p in products if p.get('brand', 'Unknown') == 'Unknown')
    print(f"\n📊 Unknown brands before: {unknown_before} ({unknown_before/len(products)*100:.1f}%)")
    
    # Fix brands
    print("\n🔧 Fixing brands...")
    fixed_count = 0
    
    for product in products:
        old_brand = product.get('brand', 'Unknown')
        
        # Only fix if Unknown
        if old_brand == 'Unknown':
            new_brand = extract_brand_smart(product.get('nome', ''))
            
            if new_brand != 'Unknown':
                product['brand'] = new_brand
                fixed_count += 1
    
    # Count after
    unknown_after = sum(1 for p in products if p.get('brand', 'Unknown') == 'Unknown')
    
    print(f"\n✅ Fixed: {fixed_count} products")
    print(f"📊 Unknown brands after: {unknown_after} ({unknown_after/len(products)*100:.1f}%)")
    print(f"📈 Improvement: {unknown_before - unknown_after} brands recognized")
    
    # Show new brand distribution
    print("\n📊 NEW BRAND DISTRIBUTION:")
    brands = Counter(p.get('brand', 'Unknown') for p in products)
    
    print(f"\nTOP 20 BRANDS:")
    for brand, count in brands.most_common(20):
        pct = count / len(products) * 100
        print(f"  {brand:30} → {count:4} ({pct:5.1f}%)")
    
    print(f"\nTotal unique brands: {len(brands)}")
    
    # Save updated file
    print("\n💾 Saving updated file...")
    
    # Backup original
    backup_file = input_file.parent / 'ALL_PRODUCTS_BACKUP.json'
    import shutil
    shutil.copy(input_file, backup_file)
    print(f"📦 Backup saved: {backup_file.name}")
    
    # Save fixed version
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved: {input_file.name}")
    
    print("\n" + "=" * 70)
    print("BRAND FIX COMPLETED!")
    print("=" * 70)
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"  Before: {unknown_before} Unknown ({unknown_before/len(products)*100:.1f}%)")
    print(f"  After:  {unknown_after} Unknown ({unknown_after/len(products)*100:.1f}%)")
    print(f"  Fixed:  {fixed_count} products")
    print(f"  Improvement: {(unknown_before - unknown_after)/unknown_before*100:.1f}% reduction in Unknown")
    print(f"  Unique brands: {len(brands)}")

if __name__ == '__main__':
    main()