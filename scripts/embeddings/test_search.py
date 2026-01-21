#!/usr/bin/env python3
"""
Search Quality Test for Glamhair Multi Comparator
Tests semantic search quality and validates FAISS index

Author: Peppe
Date: 2026-01-22
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import sys

# Numerical arrays
import numpy as np

# Embedding model
from sentence_transformers import SentenceTransformer

# Vector database
import faiss

# Import configuration
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.embeddings.embedding_config import (
    FAISS_CONFIG,
    MODEL_SPECS,
    MODEL_DOWNLOAD,
    RETRIEVAL_CONFIG,
)

# ============================================
# SEARCH ENGINE
# ============================================

class SearchEngine:
    """Semantic search engine using FAISS"""
    
    def __init__(self):
        self.index = None
        self.metadata = []
        self.model = None
        
    def load(self):
        """Load FAISS index and metadata"""
        print("📂 Loading FAISS index and metadata...")
        
        # Load FAISS index
        index_file = FAISS_CONFIG['index_file']
        if not Path(index_file).exists():
            raise FileNotFoundError(f"FAISS index not found: {index_file}")
        
        self.index = faiss.read_index(index_file)
        print(f"✅ FAISS index loaded: {self.index.ntotal} embeddings")
        
        # Load metadata
        metadata_file = FAISS_CONFIG['metadata_file']
        if not Path(metadata_file).exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        print(f"✅ Metadata loaded: {len(self.metadata)} products")
        
        # Verify consistency
        if self.index.ntotal != len(self.metadata):
            raise ValueError(f"Mismatch: {self.index.ntotal} embeddings vs {len(self.metadata)} metadata")
        
        print("✅ Index and metadata consistent\n")
        
    def load_model(self):
        """Load embedding model"""
        print(f"🤖 Loading embedding model: {MODEL_SPECS['name']}...")
        
        self.model = SentenceTransformer(
            MODEL_SPECS['name'],
            cache_folder=MODEL_DOWNLOAD['cache_dir']
        )
        
        print(f"✅ Model loaded\n")
        
    def search(self, 
               query: str, 
               top_k: int = 20,
               min_similarity: float = 0.0,
               price_max: float = None,
               categoria: str = None,
               brand: str = None) -> List[Tuple[Dict, float]]:
        """
        Search for products matching query
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_similarity: Minimum similarity score
            price_max: Maximum price filter
            categoria: Category filter
            brand: Brand filter
            
        Returns:
            List of (product_metadata, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # Reshape for FAISS
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search (get more than top_k for filtering)
        search_k = top_k * 3 if any([price_max, categoria, brand]) else top_k
        similarities, indices = self.index.search(query_embedding, search_k)
        
        # Convert to list of results
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty results
                continue
                
            if similarity < min_similarity:
                continue
            
            metadata = self.metadata[idx]
            
            # Apply filters
            if price_max and metadata['price'] > price_max:
                continue
            
            if categoria and metadata['categoria'].lower() != categoria.lower():
                continue
            
            if brand and metadata['brand'].lower() != brand.lower():
                continue
            
            results.append((metadata, float(similarity)))
            
            if len(results) >= top_k:
                break
        
        return results

# ============================================
# TEST QUERIES
# ============================================

TEST_QUERIES = [
    {
        'query': 'shampoo per capelli secchi sotto 30 euro',
        'description': 'Query with hair type and price constraint',
        'expected_category': 'haircare',
        'expected_price_max': 30,
    },
    {
        'query': 'maschera capelli danneggiati kerastase',
        'description': 'Query with brand mention',
        'expected_category': 'haircare',
        'expected_brand': 'kerastase',
    },
    {
        'query': 'olio riparatore professionale',
        'description': 'Query for professional treatment',
        'expected_category': 'haircare',
    },
    {
        'query': 'trattamento anticaduta capelli',
        'description': 'Query for specific hair concern',
        'expected_category': 'haircare',
    },
    {
        'query': 'prodotti colorazione capelli professionali',
        'description': 'Query for professional hair coloring',
        'expected_category': 'parrucchiere',
    },
    {
        'query': 'crema viso idratante acido ialuronico',
        'description': 'Query for face cream with ingredient',
        'expected_category': 'skincare',
    },
]

# ============================================
# QUALITY METRICS
# ============================================

def calculate_metrics(results: List[Tuple[Dict, float]], 
                     expected_category: str = None,
                     expected_price_max: float = None,
                     expected_brand: str = None) -> Dict:
    """Calculate quality metrics for search results"""
    
    if not results:
        return {
            'avg_similarity': 0.0,
            'category_accuracy': 0.0,
            'price_accuracy': 0.0,
            'brand_accuracy': 0.0,
            'unique_brands': 0,
        }
    
    metrics = {
        'avg_similarity': np.mean([score for _, score in results]),
        'min_similarity': min([score for _, score in results]),
        'max_similarity': max([score for _, score in results]),
    }
    
    # Category accuracy
    if expected_category:
        category_matches = sum(
            1 for product, _ in results 
            if expected_category.lower() in product['categoria'].lower()
        )
        metrics['category_accuracy'] = category_matches / len(results)
    
    # Price accuracy
    if expected_price_max:
        price_matches = sum(
            1 for product, _ in results 
            if product['price'] <= expected_price_max
        )
        metrics['price_accuracy'] = price_matches / len(results)
    
    # Brand accuracy
    if expected_brand:
        brand_matches = sum(
            1 for product, _ in results 
            if expected_brand.lower() in product['brand'].lower()
        )
        metrics['brand_accuracy'] = brand_matches / len(results)
    
    # Diversity
    unique_brands = len(set(product['brand'] for product, _ in results))
    metrics['unique_brands'] = unique_brands
    
    unique_categories = len(set(product['categoria'] for product, _ in results))
    metrics['unique_categories'] = unique_categories
    
    return metrics

# ============================================
# DISPLAY FUNCTIONS
# ============================================

def print_results(query: str, results: List[Tuple[Dict, float]], top_n: int = 10):
    """Print search results in readable format"""
    print(f"🔍 Query: \"{query}\"")
    print(f"📊 Found {len(results)} results\n")
    
    if not results:
        print("❌ No results found\n")
        return
    
    print(f"📋 Top-{min(top_n, len(results))} Results:")
    print("-" * 100)
    
    for i, (product, score) in enumerate(results[:top_n], 1):
        print(f"{i}. [Score: {score:.3f}] {product['nome']}")
        print(f"   Brand: {product['brand']} | Category: {product['categoria']} | Price: €{product['price']:.2f}")
        if i < len(results[:top_n]):
            print()
    
    print("-" * 100)

def print_metrics(metrics: Dict):
    """Print quality metrics"""
    print("\n📈 Quality Metrics:")
    print(f"   • Avg Similarity: {metrics['avg_similarity']:.3f}")
    print(f"   • Min Similarity: {metrics.get('min_similarity', 0):.3f}")
    print(f"   • Max Similarity: {metrics.get('max_similarity', 0):.3f}")
    
    if 'category_accuracy' in metrics:
        print(f"   • Category Accuracy: {metrics['category_accuracy']*100:.1f}%")
    
    if 'price_accuracy' in metrics:
        print(f"   • Price Filter Accuracy: {metrics['price_accuracy']*100:.1f}%")
    
    if 'brand_accuracy' in metrics:
        print(f"   • Brand Match: {metrics['brand_accuracy']*100:.1f}%")
    
    print(f"   • Unique Brands: {metrics['unique_brands']}")
    print(f"   • Unique Categories: {metrics.get('unique_categories', 0)}")

# ============================================
# MAIN TEST
# ============================================

def main():
    """Run all search quality tests"""
    print("=" * 100)
    print("🧪 GLAMHAIR SEARCH QUALITY TEST")
    print("=" * 100)
    print()
    
    # Initialize search engine
    engine = SearchEngine()
    
    try:
        # Load index and model
        engine.load()
        engine.load_model()
        
        # Run test queries
        print("=" * 100)
        print("🔍 TESTING SEARCH QUERIES")
        print("=" * 100)
        print()
        
        all_metrics = []
        
        for i, test in enumerate(TEST_QUERIES, 1):
            print(f"\n{'='*100}")
            print(f"TEST {i}/{len(TEST_QUERIES)}: {test['description']}")
            print('='*100)
            
            # Search
            start_time = time.time()
            results = engine.search(
                query=test['query'],
                top_k=20,
                price_max=test.get('expected_price_max'),
            )
            search_time = time.time() - start_time
            
            # Print results
            print_results(test['query'], results, top_n=10)
            
            # Calculate metrics
            metrics = calculate_metrics(
                results,
                expected_category=test.get('expected_category'),
                expected_price_max=test.get('expected_price_max'),
                expected_brand=test.get('expected_brand'),
            )
            
            print_metrics(metrics)
            print(f"\n⏱️  Search Time: {search_time*1000:.2f}ms")
            
            all_metrics.append(metrics)
        
        # Overall summary
        print("\n" + "=" * 100)
        print("📊 OVERALL SUMMARY")
        print("=" * 100)
        
        avg_similarity = np.mean([m['avg_similarity'] for m in all_metrics])
        avg_brands = np.mean([m['unique_brands'] for m in all_metrics])
        
        print(f"\n✅ Tests completed: {len(TEST_QUERIES)}")
        print(f"✅ Average similarity score: {avg_similarity:.3f}")
        print(f"✅ Average unique brands per query: {avg_brands:.1f}")
        
        # Check if quality is good
        if avg_similarity >= 0.7:
            print(f"\n🎉 EXCELLENT: Semantic search quality is HIGH (avg: {avg_similarity:.3f})")
        elif avg_similarity >= 0.5:
            print(f"\n✅ GOOD: Semantic search quality is ACCEPTABLE (avg: {avg_similarity:.3f})")
        else:
            print(f"\n⚠️  WARNING: Semantic search quality is LOW (avg: {avg_similarity:.3f})")
        
        print("\n" + "=" * 100)
        print("✅ SEARCH QUALITY TEST COMPLETE")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise

if __name__ == '__main__':
    main()