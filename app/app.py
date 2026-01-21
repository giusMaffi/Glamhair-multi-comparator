#!/usr/bin/env python3
"""
Flask Main Application
Glamhair Multi Comparator - AI Product Finder

Author: Peppe
Date: 2026-01-22
"""

import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_config
from app.session_manager import SessionManager
from src.rate_limiting.rate_limiter import RateLimiter

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flask_app')

# ============================================
# FLASK APP FACTORY
# ============================================

def create_app(config_name='development'):
    """
    Create and configure Flask application
    
    Args:
        config_name: Configuration name (development/production/testing)
        
    Returns:
        Flask app instance
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent.parent / 'templates'),
        static_folder=str(Path(__file__).parent.parent / 'static')
    )
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Initialize components
    app.session_manager = SessionManager(
        session_lifetime_minutes=config.PERMANENT_SESSION_LIFETIME // 60
    )
    
    # Initialize rate limiter (if enabled)
    if config.RATE_LIMITER_ENABLED:
        try:
            app.rate_limiter = RateLimiter(config.RATE_LIMITER_CONFIG)
            logger.info("✅ Rate limiter enabled")
        except Exception as e:
            logger.warning(f"⚠️  Rate limiter disabled: {e}")
            app.rate_limiter = None
    else:
        app.rate_limiter = None
        logger.info("ℹ️  Rate limiter disabled (development mode)")
    
    # Register routes
    from app.routes import api
    app.register_blueprint(api.bp)
    
    logger.info(f"✅ Flask app created (config: {config_name})")
    
    return app

# ============================================
# MAIN ROUTES (Root)
# ============================================

app = create_app()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    active_sessions = app.session_manager.get_active_sessions_count()
    
    health_data = {
        'status': 'healthy',
        'service': 'glamhair-multi-comparator',
        'version': '0.1.0',
        'active_sessions': active_sessions,
        'rate_limiter': 'enabled' if app.rate_limiter else 'disabled'
    }
    
    # Add rate limiter status if enabled
    if app.rate_limiter:
        try:
            limiter_status = app.rate_limiter.get_status()
            health_data['rate_limiter_status'] = limiter_status
        except Exception as e:
            logger.error(f"Error getting rate limiter status: {e}")
    
    return jsonify(health_data), 200

@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    # Cleanup expired sessions on startup
    app.session_manager.cleanup_expired_sessions()
    
    # Run Flask app
    host = '0.0.0.0'
    port = 5001
    
    logger.info(f"🚀 Starting Flask app on {host}:{port}")
    logger.info(f"📊 Environment: {app.config.get('ENV', 'development')}")
    logger.info(f"�� Debug mode: {app.config.get('DEBUG', False)}")
    
    app.run(
        host=host,
        port=port,
        debug=app.config.get('DEBUG', False)
    )
