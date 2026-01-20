"""
Central Configuration for Glamhairshop Assistant
Loads environment variables and provides app-wide config
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# Paths
# ============================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'products').mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'embeddings').mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'raw').mkdir(parents=True, exist_ok=True)

# ============================================
# Anthropic API Configuration
# ============================================
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

MODEL_NAME = os.getenv('MODEL_NAME', 'claude-sonnet-4-20250514')
MODEL_TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2000'))

# ============================================
# Flask Configuration
# ============================================
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
PORT = int(os.getenv('PORT', '5000'))
HOST = os.getenv('HOST', '0.0.0.0')

# ============================================
# RAG Configuration
# ============================================
EMBEDDING_MODEL = os.getenv(
    'EMBEDDING_MODEL',
    'paraphrase-multilingual-mpnet-base-v2'
)
TOP_K_PRODUCTS = int(os.getenv('TOP_K_PRODUCTS', '20'))
RERANK_TOP_N = int(os.getenv('RERANK_TOP_N', '10'))

# Product data paths
HAIRCARE_PRODUCTS_PATH = DATA_DIR / 'products' / 'haircare_products.json'
PARRUCCHIERE_PRODUCTS_PATH = DATA_DIR / 'products' / 'parrucchiere_products.json'

# Embeddings paths
HAIRCARE_EMBEDDINGS_PATH = DATA_DIR / 'embeddings' / 'haircare_embeddings.pkl'
PARRUCCHIERE_EMBEDDINGS_PATH = DATA_DIR / 'embeddings' / 'parrucchiere_embeddings.pkl'

# ============================================
# Categories
# ============================================
ENABLED_CATEGORIES = os.getenv('ENABLED_CATEGORIES', 'haircare,parrucchiere').split(',')

CATEGORY_CONFIG = {
    'haircare': {
        'name': 'Hair Care',
        'description': 'Prodotti per la cura dei capelli (B2C)',
        'products_path': HAIRCARE_PRODUCTS_PATH,
        'embeddings_path': HAIRCARE_EMBEDDINGS_PATH,
    },
    'parrucchiere': {
        'name': 'Parrucchiere',
        'description': 'Prodotti e attrezzature professionali (B2B)',
        'products_path': PARRUCCHIERE_PRODUCTS_PATH,
        'embeddings_path': PARRUCCHIERE_EMBEDDINGS_PATH,
    }
}

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:5000,https://www.glamhairshop.it'
).split(',')

# ============================================
# Analytics
# ============================================
UMAMI_WEBSITE_ID = os.getenv('UMAMI_WEBSITE_ID')
UMAMI_SCRIPT_URL = os.getenv(
    'UMAMI_SCRIPT_URL',
    'https://cloud.umami.is/script.js'
)

# ============================================
# Logging
# ============================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = LOGS_DIR / os.getenv('LOG_FILE', 'app.log')

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))
RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '200'))

# ============================================
# Feature Flags
# ============================================
ENABLE_COMPARATOR = os.getenv('ENABLE_COMPARATOR', 'true').lower() == 'true'
ENABLE_QUERY_ENRICHMENT = os.getenv('ENABLE_QUERY_ENRICHMENT', 'true').lower() == 'true'
ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'

# ============================================
# Languages
# ============================================
SUPPORTED_LANGUAGES = ['it', 'en', 'de', 'fr', 'es']
DEFAULT_LANGUAGE = 'it'

# ============================================
# Session Configuration
# ============================================
SESSION_TIMEOUT_MINUTES = 30
MAX_CONVERSATION_HISTORY = 10  # Keep last 10 messages

# ============================================
# Product Matching Configuration
# ============================================
MATCH_CONFIG = {
    'haircare': {
        'boost_brand_match': 1.3,
        'boost_problem_match': 1.6,
        'boost_hair_type_match': 1.4,
        'boost_goal_match': 1.3,
        'boost_budget_match': 1.2,
        'penalty_wrong_category': 0.05
    },
    'parrucchiere': {
        'boost_brand_match': 1.2,
        'boost_tool_type_match': 1.5,
        'boost_usage_match': 1.4,
        'boost_tech_match': 1.3,
        'penalty_wrong_subcategory': 0.1
    }
}

# ============================================
# Validation
# ============================================
def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == 'your-api-key':
        errors.append("ANTHROPIC_API_KEY not properly configured")
    
    if FLASK_ENV == 'production' and SECRET_KEY == 'dev-secret-key-change-in-production':
        errors.append("SECRET_KEY must be changed in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Run validation on import
validate_config()

# ============================================
# Debug Print (only in development)
# ============================================
if FLASK_DEBUG:
    print("=" * 60)
    print("GLAMHAIRSHOP ASSISTANT - Configuration Loaded")
    print("=" * 60)
    print(f"Environment: {FLASK_ENV}")
    print(f"Model: {MODEL_NAME}")
    print(f"Categories: {', '.join(ENABLED_CATEGORIES)}")
    print(f"Port: {PORT}")
    print("=" * 60)
