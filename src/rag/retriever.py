#!/usr/bin/env python3
"""
Hybrid Retriever for Glamhair Multi Comparator
Combines keyword matching + semantic search for optimal results

Author: Peppe + Claude
Date: 2026-01-22
Version: 2.0 - Hybrid Search
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from src.config import (
    DATA_DIR,
    BASE_DIR,
    EMBEDDING_MODEL,
    TOP_K_PRODUCTS,
)

logger = logging.getLogger(__name__)

MODELS_DIR = BASE_DIR / 'models'

class HybridProductRetriever:
    """
    Hybrid search combining:
    1. Keyword matching (exact brand/category matches)
    2. Semantic search (FAISS embeddings)
    
    Optimized for queries like "shampoo wella" to return ALL Wella shampoos
    """
    
    def __init__(self):
        self.index = None
        self.metadata = []
        self.model = None
        self.loaded = False
        
        self.index_file = DATA_DIR / 'embeddings' / 'faiss_index.bin'
        self.metadata_file = DATA_DIR / 'embeddings' / 'products_metadata.json'
        self.model_cache_dir = MODELS_DIR / 'embedding_model'
        
        # Brand keywords for exact matching
        self.known_brands = set()
        
        logger.info("HybridProductRetriever initialized")
    
    def load(self) -> bool:
        """Load FAISS index, metadata, and embedding model"""
        if self.loaded:
            logger.info("Retriever already loaded")
            return True
        
        try:
            logger.info("Loading FAISS index and metadata...")
            
            if not self.index_file.exists():
                logger.error(f"FAISS index not found: {self.index_file}")
                return False
            
            self.index = faiss.read_index(str(self.index_file))
            logger.info(f"✅ FAISS index loaded ({self.index.ntotal} vectors)")
            
            if not self.metadata_file.exists():
                logger.error(f"Metadata not found: {self.metadata_file}")
                return False
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"✅ Metadata loaded ({len(self.metadata)} products)")
            
            if self.index.ntotal != len(self.metadata):
                logger.error(f"Mismatch: {self.index.ntotal} vs {len(self.metadata)}")
                return False
            
            # Extract known brands
            self.known_brands = set(
                p.get('brand', '').lower().strip() 
                for p in self.metadata 
                if p.get('brand')
            )
            logger.info(f"✅ Extracted {len(self.known_brands)} unique brands")
            
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(
                EMBEDDING_MODEL,
                cache_folder=str(self.model_cache_dir)
            )
            logger.info("✅ Model loaded")
            
            self.loaded = True
            logger.info("✅ Hybrid retriever ready")
            return True
            
        except Exception as e:
            logger.error(f"Error loading retriever: {e}", exc_info=True)
            return False
    
    def _extract_filters(self, query: str) -> Dict:
        """
        Extract filters from query (brand, category, price)
        
        Examples:
            "shampoo wella" → brand: "wella"
            "phon ghd economico" → brand: "ghd", price: "low"
            "kerastase colorati" → brand: "kerastase", category: "colorati"
        """
        filters = {
            'brand': None,
            'category_keywords': [],
            'price_hint': None
        }
        
        query_lower = query.lower()
        
        # Extract brand (exact match)
        for brand in self.known_brands:
            if brand in query_lower:
                filters['brand'] = brand
                logger.info(f"🎯 Detected brand filter: {brand}")
                break
        
        # Extract category keywords
        category_keywords = [
            'shampoo', 'balsamo', 'maschera', 'trattamento',
            'olio', 'siero', 'spray', 'mousse', 'gel',
            'phon', 'piastra', 'spazzola', 'diffusore'
        ]
        
        for keyword in category_keywords:
            if keyword in query_lower:
                filters['category_keywords'].append(keyword)
        
        # Extract price hints
        if any(word in query_lower for word in ['economico', 'conveniente', 'low cost']):
            filters['price_hint'] = 'low'
        elif any(word in query_lower for word in ['premium', 'professionale', 'lusso']):
            filters['price_hint'] = 'high'
        
        return filters
    
    def _keyword_search(self, filters: Dict, top_k: int) -> List[Dict]:
        """
        Perform keyword-based filtering on metadata
        Returns products matching filters exactly
        """
        results = []
        
        brand_filter = filters.get('brand')
        category_keywords = filters.get('category_keywords', [])
        
        if not brand_filter and not category_keywords:
            return results
        
        for product in self.metadata:
            # Brand partial match (allows "wella" to match "Wella Sp")
            if brand_filter:
                product_brand = product.get('brand', '').lower().strip()
                if brand_filter not in product_brand:
                    continue
            
            # Category keyword match
            if category_keywords:
                product_nome = product.get('nome', '').lower()
                product_cat = product.get('categoria', '').lower()
                
                # At least one keyword must match
                if not any(kw in product_nome or kw in product_cat for kw in category_keywords):
                    continue
            
            # Match!
            product_copy = product.copy()
            product_copy['match_type'] = 'keyword'
            product_copy['similarity_score'] = 1.0  # Perfect keyword match
            results.append(product_copy)
        
        logger.info(f"🔍 Keyword search found {len(results)} exact matches")
        return results[:top_k]
    
    def _semantic_search(
        self,
        query: str,
        top_k: int,
        min_similarity: float,
        exclude_ids: set = None
    ) -> List[Dict]:
        """Perform semantic FAISS search"""
        try:
            query_embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            
            # Search more to account for exclusions
            search_k = top_k * 2 if exclude_ids else top_k
            similarities, indices = self.index.search(query_embedding, search_k)
            
            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:
                    continue
                
                if similarity < min_similarity:
                    continue
                
                metadata = self.metadata[idx].copy()
                
                # Skip if already in keyword results
                if exclude_ids and metadata['id'] in exclude_ids:
                    continue
                
                metadata['similarity_score'] = float(similarity)
                metadata['match_type'] = 'semantic'
                results.append(metadata)
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"🧠 Semantic search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}", exc_info=True)
            return []
    
    def search(
        self,
        query: str,
        top_k: int = None,
        min_similarity: float = 0.3,
        **kwargs
    ) -> List[Dict]:
        """
        Hybrid search combining keyword + semantic
        
        Strategy:
        1. Extract filters from query (brand, category)
        2. If filters present → keyword search first
        3. Fill remaining slots with semantic search
        4. Merge and deduplicate results
        """
        if not self.loaded:
            logger.error("Retriever not loaded")
            return []
        
        if top_k is None:
            top_k = TOP_K_PRODUCTS
        
        logger.info(f"🔎 Hybrid search: '{query[:100]}' (top_k={top_k})")
        
        # Extract filters
        filters = self._extract_filters(query)
        
        results = []
        keyword_ids = set()
        
        # PHASE 1: Keyword search (if filters present)
        if filters['brand'] or filters['category_keywords']:
            keyword_results = self._keyword_search(filters, top_k=top_k)
            results.extend(keyword_results)
            keyword_ids = {r['id'] for r in keyword_results}
            logger.info(f"✅ Phase 1 (keyword): {len(results)} results")
        
        # PHASE 2: Semantic search (fill remaining slots)
        remaining_slots = top_k - len(results)
        
        if remaining_slots > 0:
            # Lower threshold if we have keyword matches already
            semantic_threshold = min_similarity * 0.8 if keyword_ids else min_similarity
            
            semantic_results = self._semantic_search(
                query=query,
                top_k=remaining_slots,
                min_similarity=semantic_threshold,
                exclude_ids=keyword_ids
            )
            results.extend(semantic_results)
            logger.info(f"✅ Phase 2 (semantic): +{len(semantic_results)} results")
        
        # PHASE 3: Sort by relevance
        # Keyword matches first (score 1.0), then semantic by score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"🎯 Total results: {len(results)}")
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        if not self.loaded:
            return {'loaded': False}
        
        return {
            'loaded': True,
            'total_products': len(self.metadata),
            'index_size': self.index.ntotal,
            'model': EMBEDDING_MODEL,
            'known_brands': len(self.known_brands),
            'search_mode': 'hybrid (keyword + semantic)'
        }

# Global singleton
_retriever_instance = None

def get_retriever() -> HybridProductRetriever:
    """Get or create global retriever instance"""
    global _retriever_instance
    
    if _retriever_instance is None:
        logger.info("Creating hybrid retriever instance...")
        _retriever_instance = HybridProductRetriever()
        
        if not _retriever_instance.load():
            logger.error("Failed to load retriever")
            raise RuntimeError("Retriever initialization failed")
    
    return _retriever_instance

def format_products_for_context(products: List[Dict], max_products: int = 20) -> str:
    """Format product list for Claude context"""
    if not products:
        return "Nessun prodotto trovato."
    
    products = products[:max_products]
    
    header = f"# CATALOGO PRODOTTI DISPONIBILI ({len(products)} risultati)\n\n"
    
    formatted_products = []
    for i, product in enumerate(products, 1):
        parts = [f"{i}. **{product['nome']}**"]
        
        # Brand & Category
        parts.append(f"   Brand: {product['brand']}")
        parts.append(f"   Categoria: {product['categoria']}")
        
        if product.get('subcategoria'):
            parts.append(f"   Subcategoria: {product['subcategoria']}")
        
        # Pricing
        parts.append(f"   Prezzo: €{product['price']:.2f}")
        
        if product.get('promo_price'):
            parts.append(f"   Prezzo promo: €{product['promo_price']:.2f}")
            if product.get('discount_percent'):
                parts.append(f"   Sconto: {product['discount_percent']}%")
        
        # Description
        desc = product.get('descrizione_completa', '').strip()
        if desc:
            if len(desc) > 500:
                desc = desc[:497] + "..."
            parts.append(f"   **Descrizione:** {desc}")
        
        # Ingredients
        ingredienti = product.get('ingredienti', '').strip()
        if ingredienti:
            if len(ingredienti) > 300:
                ingredienti = ingredienti[:297] + "..."
            parts.append(f"   **Ingredienti:** {ingredienti}")
        
        # Usage
        modo_uso = product.get('modo_uso', '').strip()
        if modo_uso:
            if len(modo_uso) > 200:
                modo_uso = modo_uso[:197] + "..."
            parts.append(f"   **Modo d'uso:** {modo_uso}")
        
        # Image & URL
        if product.get('immagine'):
            parts.append(f"   Immagine: {product['immagine']}")
        
        parts.append(f"   Link: {product['url']}")
        
        # Match metadata
        match_type = product.get('match_type', 'unknown')
        score = product.get('similarity_score', 0)
        parts.append(f"   Relevance: {score:.2f} ({match_type})")
        
        formatted_products.append("\n".join(parts))
    
    return header + "\n\n".join(formatted_products)
