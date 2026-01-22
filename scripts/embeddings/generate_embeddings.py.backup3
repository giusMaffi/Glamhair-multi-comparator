#!/usr/bin/env python3
"""
Embeddings Generator for Glamhair Multi Comparator
Generates semantic embeddings for all products and stores in FAISS index

Author: Peppe
Date: 2026-01-22
Version: 2.0 (FAISS)
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Numerical arrays
import numpy as np

# Progress bar
from tqdm import tqdm

# Embedding model
from sentence_transformers import SentenceTransformer

# Vector database
import faiss

# Import configuration
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.embeddings.embedding_config import (
    PRODUCTS_FILE,
    FAISS_CONFIG,
    MODEL_SPECS,
    MODEL_DOWNLOAD,
    GENERATION_CONFIG,
    LOGGING_CONFIG,
    LOG_FILES,
    MONITORING_CONFIG,
    ERROR_HANDLING,
    DIAGNOSTICS_FILE,
    GENERATION_STATS_FILE,
    ensure_directories,
    get_embedding_text,
    get_price_range,
)

# ============================================
# LOGGING SETUP
# ============================================

def setup_logging():
    """Setup logging configuration"""
    ensure_directories()
    
    # Create logger
    logger = logging.getLogger('embeddings_generator')
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILES['generation'])
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(LOG_FILES['errors'])
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

logger = setup_logging()

# ============================================
# PRODUCT LOADER
# ============================================

class ProductLoader:
    """Loads and validates product data"""
    
    def __init__(self, products_file: Path):
        self.products_file = products_file
        self.products = []
        
    def load(self) -> List[Dict]:
        """Load products from JSON file"""
        logger.info(f"📂 Loading products from {self.products_file.name}...")
        
        if not self.products_file.exists():
            raise FileNotFoundError(f"Products file not found: {self.products_file}")
        
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.products)} products")
            return self.products
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON file: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading products: {e}")
            raise
    
    def validate(self) -> Dict:
        """Validate product data structure"""
        logger.info("🔍 Validating product data...")
        
        stats = {
            'total': len(self.products),
            'with_name': 0,
            'with_brand': 0,
            'with_description': 0,
            'with_price': 0,
            'with_category': 0,
            'valid': 0,
            'invalid': [],
        }
        
        required_fields = ['id', 'nome', 'brand', 'categoria']
        
        for product in self.products:
            # Count fields
            if product.get('nome'):
                stats['with_name'] += 1
            if product.get('brand'):
                stats['with_brand'] += 1
            if product.get('descrizione_completa'):
                stats['with_description'] += 1
            if product.get('regular_price'):
                stats['with_price'] += 1
            if product.get('categoria'):
                stats['with_category'] += 1
            
            # Check required fields
            if all(product.get(field) for field in required_fields):
                stats['valid'] += 1
            else:
                missing = [f for f in required_fields if not product.get(f)]
                stats['invalid'].append({
                    'id': product.get('id', 'unknown'),
                    'missing_fields': missing
                })
        
        # Log validation results
        logger.info(f"✅ Validation complete:")
        logger.info(f"   • Total products: {stats['total']}")
        logger.info(f"   • Valid products: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
        logger.info(f"   • With name: {stats['with_name']}")
        logger.info(f"   • With brand: {stats['with_brand']}")
        logger.info(f"   • With description: {stats['with_description']}")
        logger.info(f"   • With price: {stats['with_price']}")
        logger.info(f"   • With category: {stats['with_category']}")
        
        if stats['invalid']:
            logger.warning(f"⚠️  {len(stats['invalid'])} products have missing required fields")
            logger.warning(f"   First 5 invalid: {stats['invalid'][:5]}")
        
        return stats

# ============================================
# EMBEDDING MODEL
# ============================================

class EmbeddingModel:
    """Wrapper for Sentence-BERT model"""
    
    def __init__(self):
        self.model = None
        self.model_name = MODEL_SPECS['name']
        
    def initialize(self):
        """Initialize and download model if needed"""
        logger.info(f"🤖 Initializing embedding model: {self.model_name}")
        
        try:
            start_time = time.time()
            
            # Load model (will download if not cached)
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=MODEL_DOWNLOAD['cache_dir']
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
            
            # Verify model
            self._verify_model()
            
            return self.model
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise
    
    def _verify_model(self):
        """Verify model is working correctly"""
        logger.info("🔍 Verifying model...")
        
        # Test encoding
        test_text = "Test product: Shampoo per capelli secchi"
        embedding = self.model.encode(test_text)
        
        # Check dimensions
        if len(embedding) != MODEL_SPECS['dimensions']:
            raise ValueError(f"Wrong embedding dimensions: {len(embedding)} vs {MODEL_SPECS['dimensions']}")
        
        logger.info(f"✅ Model verified:")
        logger.info(f"   • Dimensions: {len(embedding)}")
        logger.info(f"   • Max sequence length: {self.model.max_seq_length}")
        logger.info(f"   • Device: {self.model.device}")
    
    def encode_batch(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """Encode a batch of texts"""
        return self.model.encode(
            texts,
            show_progress_bar=show_progress,
            batch_size=MODEL_SPECS['batch_size'],
            normalize_embeddings=MODEL_SPECS['normalize_embeddings'],
            convert_to_numpy=True
        )

# ============================================
# FAISS MANAGER
# ============================================

class FAISSManager:
    """Manages FAISS index and metadata"""
    
    def __init__(self):
        self.index = None
        self.metadata = []  # List of product metadata (order matches index)
        self.dimension = FAISS_CONFIG['dimension']
        
    def initialize(self):
        """Initialize FAISS index"""
        logger.info("💾 Initializing FAISS index...")
        
        try:
            # Create IndexFlatIP (Inner Product for normalized vectors = cosine similarity)
            self.index = faiss.IndexFlatIP(self.dimension)
            
            logger.info(f"✅ FAISS index initialized:")
            logger.info(f"   • Index type: IndexFlatIP (cosine similarity)")
            logger.info(f"   • Dimensions: {self.dimension}")
            logger.info(f"   • Initial count: {self.index.ntotal}")
            
            return self.index
            
        except Exception as e:
            logger.error(f"❌ Error initializing FAISS: {e}")
            raise
    
    def add_batch(self, embeddings: np.ndarray, metadatas: List[Dict]):
        """Add a batch of embeddings to index"""
        try:
            # Ensure embeddings are float32 (FAISS requirement)
            embeddings = embeddings.astype('float32')
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Store metadata
            self.metadata.extend(metadatas)
            
        except Exception as e:
            logger.error(f"❌ Error adding batch to FAISS: {e}")
            raise
    
    def get_count(self) -> int:
        """Get total count of embeddings in index"""
        return self.index.ntotal
    
    def save(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, FAISS_CONFIG['index_file'])
            logger.info(f"✅ FAISS index saved to {FAISS_CONFIG['index_file']}")
            
            # Save metadata
            with open(FAISS_CONFIG['metadata_file'], 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Metadata saved to {FAISS_CONFIG['metadata_file']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving FAISS index/metadata: {e}")
            raise
    
    def verify_integrity(self, expected_count: int) -> bool:
        """Verify index integrity"""
        actual_count = self.get_count()
        metadata_count = len(self.metadata)
        
        if actual_count == expected_count == metadata_count:
            logger.info(f"✅ FAISS integrity verified: {actual_count} embeddings")
            return True
        else:
            logger.error(f"❌ FAISS integrity check failed:")
            logger.error(f"   Index count: {actual_count}")
            logger.error(f"   Metadata count: {metadata_count}")
            logger.error(f"   Expected: {expected_count}")
            return False

# ============================================
# EMBEDDINGS GENERATOR
# ============================================

class EmbeddingsGenerator:
    """Main embeddings generation pipeline"""
    
    def __init__(self):
        self.products = []
        self.loader = ProductLoader(PRODUCTS_FILE)
        self.model = EmbeddingModel()
        self.faiss = FAISSManager()
        
        self.stats = {
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'total_products': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'failed_products': [],
            'batches_processed': 0,
            'avg_time_per_batch': 0,
            'avg_time_per_product': 0,
        }
    
    def run(self):
        """Run the complete embedding generation pipeline"""
        logger.info("=" * 60)
        logger.info("🚀 GLAMHAIR EMBEDDINGS GENERATION (FAISS)")
        logger.info("=" * 60)
        
        self.stats['start_time'] = datetime.now()
        
        try:
            # Step 1: Load products
            self.products = self.loader.load()
            validation_stats = self.loader.validate()
            self.stats['total_products'] = len(self.products)
            
            # Step 2: Initialize model
            self.model.initialize()
            
            # Step 3: Initialize FAISS
            self.faiss.initialize()
            
            # Step 4: Generate embeddings
            self._generate_embeddings()
            
            # Step 5: Save FAISS index and metadata
            self._save_index()
            
            # Step 6: Verify integrity
            self._verify_integrity()
            
            # Step 7: Save diagnostics
            self._save_diagnostics()
            
            # Step 8: Final summary
            self._print_summary()
            
            logger.info("=" * 60)
            logger.info("✅ EMBEDDINGS GENERATION COMPLETE")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Fatal error in embedding generation: {e}")
            raise
        finally:
            self.stats['end_time'] = datetime.now()
            if self.stats['start_time']:
                self.stats['duration'] = (
                    self.stats['end_time'] - self.stats['start_time']
                ).total_seconds()
    
    def _generate_embeddings(self):
        """Generate embeddings for all products in batches"""
        logger.info(f"\n🔄 Generating embeddings for {len(self.products)} products...")
        logger.info(f"   • Batch size: {GENERATION_CONFIG['batch_size']}")
        logger.info(f"   • Model: {MODEL_SPECS['name']}")
        
        batch_size = GENERATION_CONFIG['batch_size']
        num_batches = (len(self.products) + batch_size - 1) // batch_size
        
        batch_times = []
        
        # Process in batches with progress bar
        with tqdm(total=len(self.products), desc="Generating embeddings") as pbar:
            for batch_idx in range(num_batches):
                batch_start = batch_idx * batch_size
                batch_end = min((batch_idx + 1) * batch_size, len(self.products))
                batch_products = self.products[batch_start:batch_end]
                
                batch_start_time = time.time()
                
                try:
                    # Process batch
                    self._process_batch(batch_products, batch_idx)
                    
                    batch_time = time.time() - batch_start_time
                    batch_times.append(batch_time)
                    
                    self.stats['batches_processed'] += 1
                    
                    # Log progress
                    if (batch_idx + 1) % GENERATION_CONFIG['log_every_n_batches'] == 0:
                        avg_time = sum(batch_times[-5:]) / len(batch_times[-5:])
                        logger.info(
                            f"   Batch {batch_idx + 1}/{num_batches} | "
                            f"Avg time: {avg_time:.2f}s | "
                            f"Products: {self.stats['successful']}/{self.stats['total_products']}"
                        )
                    
                    pbar.update(len(batch_products))
                    
                except Exception as e:
                    logger.error(f"❌ Error processing batch {batch_idx}: {e}")
                    # Continue with next batch
                    continue
        
        # Calculate averages
        if batch_times:
            self.stats['avg_time_per_batch'] = sum(batch_times) / len(batch_times)
            self.stats['avg_time_per_product'] = (
                sum(batch_times) / self.stats['successful']
            )
    
    def _process_batch(self, batch_products: List[Dict], batch_idx: int):
        """Process a single batch of products"""
        
        # Prepare data
        texts = []
        metadatas = []
        
        for product in batch_products:
            try:
                # Generate embedding text
                embedding_text = get_embedding_text(product)
                
                # Prepare metadata
                metadata = {
                    'id': product.get('id', f"UNKNOWN_{self.stats['processed']}"),
                    'nome': product.get('nome', ''),
                    'brand': product.get('brand', ''),
                    'categoria': product.get('categoria', ''),
                    'price': float(product.get('regular_price', 0)),
                    'price_range': get_price_range(float(product.get('regular_price', 0))),
                    'url': product.get('url', ''),
                    'immagine': product.get('immagine', ''),
                }
                
                texts.append(embedding_text)
                metadatas.append(metadata)
                
                self.stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Error preparing product {product.get('id', 'unknown')}: {e}")
                self.stats['failed'] += 1
                self.stats['failed_products'].append({
                    'id': product.get('id', 'unknown'),
                    'error': str(e)
                })
                continue
        
        if not texts:
            logger.warning(f"⚠️  Batch {batch_idx} has no valid products, skipping")
            return
        
        try:
            # Generate embeddings
            embeddings = self.model.encode_batch(texts, show_progress=False)
            
            # Add to FAISS
            self.faiss.add_batch(embeddings, metadatas)
            
            self.stats['successful'] += len(texts)
            
        except Exception as e:
            logger.error(f"❌ Error encoding/storing batch {batch_idx}: {e}")
            raise
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        logger.info("\n💾 Saving FAISS index and metadata...")
        self.faiss.save()
    
    def _verify_integrity(self):
        """Verify FAISS integrity"""
        logger.info("\n🔍 Verifying FAISS integrity...")
        
        is_valid = self.faiss.verify_integrity(self.stats['successful'])
        
        if not is_valid:
            logger.error("❌ Integrity check failed!")
            raise ValueError("FAISS integrity check failed")
    
    def _save_diagnostics(self):
        """Save generation diagnostics"""
        logger.info("\n💾 Saving diagnostics...")
        
        diagnostics = {
            'generation_date': datetime.now().isoformat(),
            'duration_seconds': self.stats['duration'],
            'stats': self.stats,
            'config': {
                'model': MODEL_SPECS['name'],
                'dimensions': MODEL_SPECS['dimensions'],
                'batch_size': GENERATION_CONFIG['batch_size'],
                'index_type': 'FAISS IndexFlatIP',
                'index_file': FAISS_CONFIG['index_file'],
                'metadata_file': FAISS_CONFIG['metadata_file'],
            }
        }
        
        # Save diagnostics
        with open(DIAGNOSTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Diagnostics saved to {DIAGNOSTICS_FILE}")
        
        # Save generation stats
        with open(GENERATION_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Stats saved to {GENERATION_STATS_FILE}")
    
    def _print_summary(self):
        """Print final summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {self.stats['duration']:.2f} seconds ({self.stats['duration']/60:.2f} minutes)")
        logger.info(f"📦 Total products: {self.stats['total_products']}")
        logger.info(f"✅ Successfully processed: {self.stats['successful']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"📊 Success rate: {self.stats['successful']/self.stats['total_products']*100:.2f}%")
        logger.info(f"⚡ Batches processed: {self.stats['batches_processed']}")
        logger.info(f"⏱️  Avg time per batch: {self.stats['avg_time_per_batch']:.2f}s")
        logger.info(f"⏱️  Avg time per product: {self.stats['avg_time_per_product']:.3f}s")
        
        if self.stats['failed_products']:
            logger.warning(f"\n⚠️  Failed products: {len(self.stats['failed_products'])}")
            logger.warning(f"   First 5: {self.stats['failed_products'][:5]}")
        
        logger.info("\n💾 Output:")
        logger.info(f"   • FAISS index: {FAISS_CONFIG['index_file']}")
        logger.info(f"   • Metadata: {FAISS_CONFIG['metadata_file']}")
        logger.info(f"   • Diagnostics: {DIAGNOSTICS_FILE}")
        logger.info(f"   • Stats: {GENERATION_STATS_FILE}")
        logger.info("=" * 60)

# ============================================
# MAIN
# ============================================

def main():
    """Main entry point"""
    generator = EmbeddingsGenerator()
    generator.run()

if __name__ == '__main__':
    main()