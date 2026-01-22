#!/usr/bin/env python3
"""
RAG Retriever for Glamhair Multi Comparator
Production-ready wrapper for FAISS semantic search

Author: Peppe
Date: 2026-01-21
Version: 1.0
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Import config
from src.config import (
    DATA_DIR,
    BASE_DIR,
    EMBEDDING_MODEL,
    TOP_K_PRODUCTS,
)

# Setup logging
logger = logging.getLogger(__name__)

# Paths
MODELS_DIR = BASE_DIR / 'models'

class ProductRetriever:
    """Semantic search retriever using FAISS"""
    
    def __init__(self):
        self.index = None
        self.metadata = []
        self.model = None
        self.is_loaded = False
        
        self.index_file = DATA_DIR / 'embeddings' / 'faiss_index.bin'
        self.metadata_file = DATA_DIR / 'embeddings' / 'products_metadata.json'
        self.model_cache_dir = MODELS_DIR / 'embedding_model'
        
        logger.info("ProductRetriever initialized")
    
    def load(self) -> bool:
        """Load FAISS index, metadata, and embedding model"""
        if self.is_loaded:
            logger.info("Retriever already loaded")
            return True
        
        try:
            logger.info("Loading FAISS index and metadata...")
            
            if not self.index_file.exists():
                logger.error(f"FAISS index not found: {self.index_file}")
                return False
            
            self.index = faiss.read_index(str(self.index_file))
            logger.info(f"✅ FAISS index loaded: {self.index.ntotal} embeddings")
            
            if not self.metadata_file.exists():
                logger.error(f"Metadata not found: {self.metadata_file}")
                return False
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"✅ Metadata loaded: {len(self.metadata)} products")
            
            if self.index.ntotal != len(self.metadata):
                logger.error(f"Mismatch: {self.index.ntotal} vs {len(self.metadata)}")
                return False
            
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(
                EMBEDDING_MODEL,
                cache_folder=str(self.model_cache_dir)
            )
            logger.info("✅ Model loaded")
            
            self.is_loaded = True
            logger.info("✅ Retriever ready")
            return True
            
        except Exception as e:
            logger.error(f"Error loading retriever: {e}", exc_info=True)
            return False
    
    def search(
        self,
        query: str,
        top_k: int = None,
        min_similarity: float = 0.3,
        price_max: float = None,
        categoria: str = None,
        brand: str = None
    ) -> List[Dict]:
        """Search for products matching query"""
        if not self.is_loaded:
            logger.error("Retriever not loaded")
            return []
        
        if top_k is None:
            top_k = TOP_K_PRODUCTS
        
        try:
            logger.info(f"Searching: '{query[:100]}' (top_k={top_k})")
            
            query_embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            
            search_k = top_k * 3 if any([price_max, categoria, brand]) else top_k
            similarities, indices = self.index.search(query_embedding, search_k)
            
            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:
                    continue
                
                if similarity < min_similarity:
                    continue
                
                metadata = self.metadata[idx].copy()
                metadata['similarity_score'] = float(similarity)
                
                if price_max and metadata['price'] > price_max:
                    continue
                
                if categoria and metadata['categoria'].lower() != categoria.lower():
                    continue
                
                if brand and metadata['brand'].lower() != brand.lower():
                    continue
                
                results.append(metadata)
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        if not self.is_loaded:
            return {'loaded': False}
        
        return {
            'loaded': True,
            'total_products': len(self.metadata),
            'index_size': self.index.ntotal,
            'model': EMBEDDING_MODEL,
        }

_retriever_instance = None

def get_retriever() -> ProductRetriever:
    """Get or create global retriever instance"""
    global _retriever_instance
    
    if _retriever_instance is None:
        logger.info("Creating retriever instance...")
        _retriever_instance = ProductRetriever()
        
        if not _retriever_instance.load():
            logger.error("Failed to load retriever")
            raise RuntimeError("Retriever initialization failed")
    
    return _retriever_instance

def format_products_for_context(products: List[Dict], max_products: int = 20) -> str:
    """Format product list for Claude context"""
    if not products:
        return "Nessun prodotto trovato."
    
    products = products[:max_products]
    
    formatted_products = []
    for i, product in enumerate(products, 1):
        product_text = (
            f"{i}. {product['nome']}\n"
            f"   Brand: {product['brand']}\n"
            f"   Categoria: {product['categoria']}\n"
            f"   Prezzo: €{product['price']:.2f}\n"
            f"   Relevance: {product.get('similarity_score', 0):.2f}\n"
            f"   ID: {product['id']}\n"
            f"   URL: {product['url']}"
        )
        formatted_products.append(product_text)
    
    return "\n\n".join(formatted_products)
