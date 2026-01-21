#!/usr/bin/env python3
"""
Flask Application Configuration
Glamhair Multi Comparator

Author: Peppe
Date: 2026-01-22
"""

import os
import secrets
from pathlib import Path

# Import from core config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import ANTHROPIC_API_KEY, BASE_DIR, DATA_DIR, LOGS_DIR

# ============================================
# APP PATHS
# ============================================

APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR.parent / 'templates'
STATIC_DIR = APP_DIR.parent / 'static'
CONFIG_DIR = BASE_DIR / 'config'
MODELS_DIR = BASE_DIR / 'models'

# ============================================
# FLASK BASE CONFIG
# ============================================

class Config:
    """Base Flask configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = False
    TESTING = False
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    
    # Rate Limiter
    RATE_LIMITER_CONFIG = str(CONFIG_DIR / 'rate_limits.yaml')
    RATE_LIMITER_ENABLED = True
    
    # Embeddings & Search (from src/config)
    EMBEDDINGS_PATH = str(MODELS_DIR / 'embeddings' / 'product_embeddings.pkl')
    PRODUCTS_PATH = str(DATA_DIR / 'products' / 'final_products.json')
    
    # Claude API (from src/config)
    ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
    CLAUDE_MODEL = 'claude-sonnet-4-20250514'
    CLAUDE_MAX_TOKENS = 4096
    CLAUDE_TEMPERATURE = 1.0
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = str(LOGS_DIR / 'app.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CORS_ORIGINS = ['*']  # Allow all origins in development
    RATE_LIMITER_ENABLED = False  # Disable rate limiting in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    RATE_LIMITER_ENABLED = True
    # Override with environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    RATE_LIMITER_ENABLED = False

# ============================================
# CONFIG SELECTOR
# ============================================

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(env, DevelopmentConfig)