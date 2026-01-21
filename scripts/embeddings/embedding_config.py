#!/usr/bin/env python3
"""
Embedding Configuration for Glamhair Multi Comparator
Centralizes all embeddings-related settings and cost optimization parameters

Author: Peppe
Date: 2026-01-22
Version: 2.0 (FAISS)
"""

from pathlib import Path
import os

# ============================================
# PROJECT PATHS
# ============================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
MODELS_DIR = PROJECT_ROOT / 'models'

# Input data
PRODUCTS_FILE = DATA_DIR / 'products' / 'ALL_PRODUCTS_ENRICHED.json'

# Output directories (will be auto-created)
EMBEDDINGS_DIR = DATA_DIR / 'embeddings'
METADATA_DIR = EMBEDDINGS_DIR / 'metadata'
EMBEDDINGS_LOGS_DIR = LOGS_DIR / 'embeddings'

# Model cache directory
MODEL_CACHE_DIR = MODELS_DIR / 'embedding_model'

# ============================================
# EMBEDDING MODEL CONFIGURATION
# ============================================
EMBEDDING_MODEL = 'paraphrase-multilingual-mpnet-base-v2'

# Model specifications
MODEL_SPECS = {
    'name': EMBEDDING_MODEL,
    'dimensions': 768,
    'max_seq_length': 384,  # tokens
    'languages': ['it', 'en', 'fr', 'de', 'es', 'pt', 'nl', 'pl', 'ru', 'zh'],
    'batch_size': 32,
    'normalize_embeddings': True,
}

# Download settings
MODEL_DOWNLOAD = {
    'cache_dir': str(MODEL_CACHE_DIR),
    'force_download': False,  # Use cached if available
    'show_progress': True,
}

# ============================================
# FAISS CONFIGURATION
# ============================================
FAISS_CONFIG = {
    'index_type': 'IndexFlatIP',  # Inner Product (cosine similarity with normalized vectors)
    'index_file': str(EMBEDDINGS_DIR / 'faiss_index.bin'),
    'metadata_file': str(EMBEDDINGS_DIR / 'products_metadata.json'),
    'dimension': 768,  # Must match model dimensions
}

# Metadata fields to store (for efficient filtering)
METADATA_FIELDS = [
    'id',
    'nome',
    'brand',
    'categoria',
    'price',
    'price_range',
    'url',
    'immagine',
]

# ============================================
# EMBEDDING GENERATION SETTINGS
# ============================================
GENERATION_CONFIG = {
    'batch_size': 100,  # Products per batch
    'show_progress': True,
    'log_every_n_batches': 5,
    'save_checkpoint_every_n_batches': 10,  # For recovery
}

# Text preparation for embeddings
TEXT_PREPARATION = {
    'max_description_length': 500,   # Chars from descrizione_completa
    'max_ingredienti_length': 300,   # Chars from ingredienti
    'max_benefici_length': 200,      # Chars from benefici
    'include_fields': [
        'nome',
        'brand',
        'categoria',
        'descrizione_completa',
        'ingredienti',
        'benefici',
        'tecnologie',
        'regular_price',
    ],
}

# ============================================
# COST OPTIMIZATION & TOKEN TRACKING
# ============================================

# Dual-context architecture (as discussed)
RETRIEVAL_CONFIG = {
    'initial_retrieval': 50,   # Broad semantic search
    'after_reranking': 20,     # Final products to Claude
}

# Token estimation (for cost tracking)
TOKEN_ESTIMATION = {
    # Minimal format (for cached catalog)
    'per_product_minimal': 200,  # ID, nome, brand, categoria, prezzo
    
    # Detailed format (for top-20 context)
    'per_product_detailed': 500,  # Full: descrizione, ingredienti, benefici
    
    # System prompt (will be cached)
    'system_prompt': 5000,
    
    # Full catalog minimal (will be cached)
    'full_catalog_cached': 2619 * 200,  # ~524k tokens
    
    # Top-20 detailed (NOT cached, per query)
    'top_20_context': 20 * 500,  # ~10k tokens
    
    # Conversation history average
    'conversation_history': 2000,
}

# Cost per call estimation (Claude Sonnet 4)
COST_ESTIMATION = {
    # Input costs
    'input_no_cache_per_1m': 3.00,      # $3/M tokens
    'input_cache_write_per_1m': 3.75,   # $3.75/M tokens
    'input_cache_read_per_1m': 0.30,    # $0.30/M tokens
    
    # Output costs
    'output_per_1m': 15.00,             # $15/M tokens
    
    # Estimated per-call breakdown
    'per_call': {
        'input_cached': 524_000,        # Full catalog (cached)
        'input_fresh': 12_000,          # Top-20 + history + query
        'output': 500,                  # Response
        
        # Cost calculation (with cache hit)
        'cost_cached': 524_000 * 0.30 / 1_000_000,      # $0.157
        'cost_fresh': 12_000 * 3.00 / 1_000_000,        # $0.036
        'cost_output': 500 * 15.00 / 1_000_000,         # $0.0075
        'total': 0.051,  # ~$0.051 per call
    },
}

# Daily/monthly budgets (for rate limiting)
BUDGET_LIMITS = {
    'max_cost_per_day': 60.00,      # $60/day
    'max_cost_per_month': 1500.00,  # $1,500/month
    'max_conversations_per_day': 1000,
}

# ============================================
# SEARCH QUALITY SETTINGS
# ============================================
SEARCH_CONFIG = {
    'similarity_threshold': 0.5,  # Minimum cosine similarity
    'max_results': 50,            # Maximum results to return
    'enable_mmr': False,          # Maximal Marginal Relevance (diversity)
    'mmr_lambda': 0.5,            # Balance relevance vs diversity
}

# Reranking weights (for intelligent reranking)
RERANKING_WEIGHTS = {
    'semantic_similarity': 1.0,    # Base score from vector search
    'price_match': 0.3,            # Boost if within budget
    'brand_preference': 0.2,       # Boost for mentioned brands
    'category_exact': 0.4,         # Boost for exact category match
    'in_stock': 0.1,               # Future: boost in-stock items
}

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S',
    'log_to_file': True,
    'log_to_console': True,
}

# Log files
LOG_FILES = {
    'generation': EMBEDDINGS_LOGS_DIR / 'generation.log',
    'errors': EMBEDDINGS_LOGS_DIR / 'errors.log',
    'costs': EMBEDDINGS_LOGS_DIR / 'costs.log',
}

# ============================================
# MONITORING & DIAGNOSTICS
# ============================================
MONITORING_CONFIG = {
    'track_generation_time': True,
    'track_memory_usage': True,
    'track_token_usage': True,
    'track_costs': True,
    'save_diagnostics': True,
}

# Diagnostics output
DIAGNOSTICS_FILE = METADATA_DIR / 'diagnostics.json'
GENERATION_STATS_FILE = METADATA_DIR / 'generation_stats.json'

# ============================================
# ERROR HANDLING
# ============================================
ERROR_HANDLING = {
    'max_retries': 3,
    'retry_delay': 5,  # seconds
    'skip_on_error': True,  # Skip failed products instead of crashing
    'save_failed_products': True,
    'failed_products_file': METADATA_DIR / 'failed_products.json',
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def ensure_directories():
    """Create all required directories if they don't exist"""
    directories = [
        DATA_DIR,
        EMBEDDINGS_DIR,
        METADATA_DIR,
        EMBEDDINGS_LOGS_DIR,
        MODELS_DIR,
        MODEL_CACHE_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ready: {directory}")

def get_embedding_text(product: dict) -> str:
    """
    Prepare text for embedding from product data
    Optimized for search quality + token efficiency
    
    Args:
        product: Product dictionary with all fields
        
    Returns:
        Formatted text ready for embedding (target: ~300-400 chars)
    """
    prep = TEXT_PREPARATION
    
    # Extract and truncate fields
    nome = product.get('nome', '')
    brand = product.get('brand', '')
    categoria = product.get('categoria', '')
    descrizione = product.get('descrizione_completa', '')[:prep['max_description_length']]
    ingredienti = product.get('ingredienti', '')[:prep['max_ingredienti_length']]
    benefici = product.get('benefici', '')[:prep['max_benefici_length']]
    tecnologie = product.get('tecnologie', '')
    prezzo = product.get('regular_price', '')
    
    # Format text
    text_parts = [
        nome,
        f"Brand: {brand}",
        f"Categoria: {categoria}",
        descrizione,
    ]
    
    if ingredienti:
        text_parts.append(f"Ingredienti: {ingredienti}")
    
    if benefici:
        text_parts.append(f"Benefici: {benefici}")
    
    if tecnologie:
        text_parts.append(f"Tecnologie: {tecnologie}")
    
    if prezzo:
        text_parts.append(f"Prezzo: €{prezzo}")
    
    return "\n".join(text_parts).strip()

def get_price_range(price: float) -> str:
    """
    Categorize price into range for filtering
    
    Args:
        price: Product price in euros
        
    Returns:
        Price range category
    """
    if price < 20:
        return '0-20'
    elif price < 50:
        return '20-50'
    elif price < 100:
        return '50-100'
    else:
        return '100+'

def estimate_total_cost(num_conversations: int, cache_hit_rate: float = 0.95) -> dict:
    """
    Estimate total cost for N conversations
    
    Args:
        num_conversations: Number of conversations to estimate
        cache_hit_rate: Expected cache hit rate (0.95 = 95%)
        
    Returns:
        Cost breakdown dictionary
    """
    cost_per_call = COST_ESTIMATION['per_call']
    
    # First call: cache write
    first_call_cost = (
        cost_per_call['input_cached'] * COST_ESTIMATION['input_cache_write_per_1m'] / 1_000_000 +
        cost_per_call['cost_fresh'] +
        cost_per_call['cost_output']
    )
    
    # Subsequent calls: cache read
    cached_call_cost = cost_per_call['total']
    
    # Calculate total
    num_cached_calls = int(num_conversations * cache_hit_rate)
    num_uncached_calls = num_conversations - num_cached_calls
    
    total_cost = (
        num_uncached_calls * first_call_cost +
        num_cached_calls * cached_call_cost
    )
    
    return {
        'total_conversations': num_conversations,
        'cache_hit_rate': cache_hit_rate,
        'uncached_calls': num_uncached_calls,
        'cached_calls': num_cached_calls,
        'cost_per_uncached': first_call_cost,
        'cost_per_cached': cached_call_cost,
        'total_cost': total_cost,
        'cost_per_conversation_avg': total_cost / num_conversations,
    }

# ============================================
# VALIDATION
# ============================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check if products file exists
    if not PRODUCTS_FILE.exists():
        errors.append(f"Products file not found: {PRODUCTS_FILE}")
    
    # Check batch sizes are reasonable
    if GENERATION_CONFIG['batch_size'] > 500:
        errors.append("Batch size too large (max 500 recommended)")
    
    # Check cost limits are set
    if BUDGET_LIMITS['max_cost_per_day'] <= 0:
        errors.append("Invalid daily cost limit")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    print("✅ Configuration valid")
    return True

# ============================================
# INITIALIZATION
# ============================================

if __name__ == '__main__':
    """Test configuration and create directories"""
    print("🔧 Glamhair Embeddings Configuration")
    print("=" * 50)
    
    print("\n📁 Creating directories...")
    ensure_directories()
    
    print("\n✅ Validating configuration...")
    validate_config()
    
    print("\n📊 Configuration Summary:")
    print(f"   • Model: {EMBEDDING_MODEL}")
    print(f"   • Dimensions: {MODEL_SPECS['dimensions']}")
    print(f"   • Products file: {PRODUCTS_FILE}")
    print(f"   • FAISS index: {FAISS_CONFIG['index_file']}")
    print(f"   • Metadata file: {FAISS_CONFIG['metadata_file']}")
    print(f"   • Batch size: {GENERATION_CONFIG['batch_size']}")
    
    print("\n💰 Cost Estimation (per call):")
    cost = COST_ESTIMATION['per_call']
    print(f"   • Input cached: ${cost['cost_cached']:.4f}")
    print(f"   • Input fresh: ${cost['cost_fresh']:.4f}")
    print(f"   • Output: ${cost['cost_output']:.4f}")
    print(f"   • Total: ${cost['total']:.4f}")
    
    print("\n💰 Cost Projections:")
    for num_conv in [100, 500, 1000]:
        estimate = estimate_total_cost(num_conv)
        print(f"   • {num_conv} conversations: ${estimate['total_cost']:.2f} (${estimate['cost_per_conversation_avg']:.4f}/conv)")
    
    print("\n✅ Configuration ready!")