#!/usr/bin/env python3
"""
RAG Retriever - FAISS-based semantic search
Version: 2.1 - Fixed product context formatting with full descriptions

Author: Peppe
Date: 2026-01-22
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger('src.rag.retriever')

# ============================================
# CONFIGURATION
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / 'data' / 'embeddings'
FAISS_INDEX_PATH = EMBEDDINGS_DIR / 'faiss_index.bin'
METADATA_PATH = EMBEDDINGS_DIR / 'products_metadata.json'

MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

# ============================================
# RETRIEVER CLASS
# ============================================

class ProductRetriever:
    """Semantic search retriever using FAISS"""
    
    def __init__(
        self,
        index_path: Path = FAISS_INDEX_PATH,
        metadata_path: Path = METADATA_PATH,
        model_name: str = MODEL_NAME
    ):
        """Initialize retriever"""
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model_name = model_name
        
        self.index = None
        self.products_metadata = None
        self.model = None
        
        self._load_index()
        self._load_metadata()
        self._load_model()
        
        logger.info("✅ Retriever ready")
    
    def _load_index(self):
        """Load FAISS index"""
        import faiss
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {self.index_path}")
        
        self.index = faiss.read_index(str(self.index_path))
        logger.info(f"✅ FAISS index loaded ({self.index.ntotal} vectors)")
    
    def _load_metadata(self):
        """Load products metadata"""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.products_metadata = json.load(f)
        
        logger.info(f"✅ Metadata loaded ({len(self.products_metadata)} products)")
    
    def _load_model(self):
        """Load embedding model"""
        self.model = SentenceTransformer(self.model_name)
        logger.info("✅ Model loaded")
    
    def search(
        self,
        query: str,
        top_k: int = 20,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Search products by semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of product dicts with similarity scores
        """
        logger.info(f"Searching: '{query}' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        
        # Search FAISS
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Convert distances to similarity scores (cosine similarity)
        similarities = 1 - (distances[0] / 2)
        
        # Build results
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if similarity < min_similarity:
                continue
            
            if idx >= len(self.products_metadata):
                logger.warning(f"Index {idx} out of range for metadata")
                continue
            
            product = self.products_metadata[idx].copy()
            product['similarity_score'] = float(similarity)
            results.append(product)
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        return {
            'total_products': len(self.products_metadata) if self.products_metadata else 0,
            'index_size': self.index.ntotal if self.index else 0,
            'model': self.model_name,
            'index_path': str(self.index_path),
            'metadata_path': str(self.metadata_path)
        }


# ============================================
# SINGLETON INSTANCE
# ============================================

_retriever_instance = None

def get_retriever() -> ProductRetriever:
    """Get or create retriever singleton"""
    global _retriever_instance
    
    if _retriever_instance is None:
        _retriever_instance = ProductRetriever()
    
    return _retriever_instance


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def format_products_for_context(products: List[Dict], max_products: int = 20) -> str:
    """
    Format product list for Claude context with COMPLETE information
    
    CRITICAL: Include ALL product details so Claude can make informed recommendations
    """
    if not products:
        return "Nessun prodotto trovato."
    
    products = products[:max_products]
    
    formatted_products = []
    for i, product in enumerate(products, 1):
        # Start with basic info
        product_text = [
            f"## PRODOTTO {i}",
            f"**Nome:** {product['nome']}",
            f"**Brand:** {product['brand']}",
            f"**Categoria:** {product['categoria']}",
        ]
        
        # Price handling with fallback
        price = product.get('price')
        if price and price > 0:
            product_text.append(f"**Prezzo:** €{price:.2f}")
        else:
            product_text.append("**Prezzo:** Non disponibile")
        
        # Add product ID and URL
        product_text.append(f"**ID Prodotto:** {product['id']}")
        product_text.append(f"**Link:** {product['url']}")
        
        # CRITICAL: Add full description if available
        desc = product.get('descrizione_completa', '').strip()
        if desc:
            # Truncate if too long (max 500 chars to save tokens)
            if len(desc) > 500:
                desc = desc[:497] + "..."
            product_text.append(f"**Descrizione:** {desc}")
        
        # Add ingredients if available
        ingredienti = product.get('ingredienti', '').strip()
        if ingredienti:
            if len(ingredienti) > 300:
                ingredienti = ingredienti[:297] + "..."
            product_text.append(f"**Ingredienti:** {ingredienti}")
        
        # Add usage instructions if available
        modo_uso = product.get('modo_uso', '').strip()
        if modo_uso:
            if len(modo_uso) > 200:
                modo_uso = modo_uso[:197] + "..."
            product_text.append(f"**Utilizzo:** {modo_uso}")
        
        # Add image URL if available
        immagine = product.get('immagine', '').strip()
        if immagine:
            product_text.append(f"**Immagine:** {immagine}")
        
        # Add similarity score for debugging
        similarity = product.get('similarity_score', 0)
        product_text.append(f"**Relevance Score:** {similarity:.3f}")
        
        formatted_products.append("\n".join(product_text))
    
    # Add header
    header = f"# CATALOGO PRODOTTI DISPONIBILI ({len(products)} risultati)\n"
    header += "=" * 60 + "\n\n"
    
    return header + "\n\n".join(formatted_products)


# ============================================
# MAIN (for testing)
# ============================================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test retriever
    retriever = get_retriever()
    
    # Test search
    query = "shampoo wella per capelli grassi"
    results = retriever.search(query, top_k=5)
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    for product in results:
        print(f"{product['nome']}")
        print(f"  Brand: {product['brand']}")
        print(f"  Score: {product['similarity_score']:.3f}")
        print()
    
    # Test formatting
    formatted = format_products_for_context(results)
    print(f"\n{'='*60}")
    print("FORMATTED CONTEXT:")
    print(f"{'='*60}\n")
    print(formatted)
