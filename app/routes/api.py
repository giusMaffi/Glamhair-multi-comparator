#!/usr/bin/env python3
"""
API Routes
Chat endpoints for Glamhair Multi Comparator

Author: Peppe
Date: 2026-01-22
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger('api_routes')

# ============================================
# BLUEPRINT
# ============================================

bp = Blueprint('api', __name__, url_prefix='/api')

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_client_ip():
    """Get client IP address (handles proxies)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

# ============================================
# API ENDPOINTS
# ============================================

@bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Start new conversation session
    
    Returns:
        {
            'session_id': str,
            'message': str
        }
    """
    try:
        ip_address = get_client_ip()
        session_id = current_app.session_manager.create_session(ip_address)
        
        logger.info(f"Session started: {session_id[:8]}... (IP: {ip_address})")
        
        return jsonify({
            'session_id': session_id,
            'message': 'Session created successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        return jsonify({'error': 'Failed to create session'}), 500

@bp.route('/chat', methods=['POST'])
def chat():
    """
    Send message and get AI response
    
    Request:
        {
            'session_id': str,
            'message': str
        }
        
    Returns:
        {
            'response': str,
            'session_id': str
        }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        user_message = data.get('message')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        if not user_message:
            return jsonify({'error': 'message required'}), 400
        
        # Get client IP
        ip_address = get_client_ip()
        
        # Check rate limiting (if enabled)
        if current_app.rate_limiter:
            rate_check = current_app.rate_limiter.check_request(
                ip_address, 
                session_id,
                estimated_cost=0.051  # Average cost per request
            )
            
            if not rate_check['allowed']:
                logger.warning(f"Rate limit exceeded: {ip_address} - {rate_check['reason']}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'reason': rate_check['reason'],
                    'message': rate_check.get('message', 'Too many requests'),
                    'retry_after': rate_check.get('retry_after', 60)
                }), 429
        
        # Verify session exists
        session = current_app.session_manager.get_session(session_id)
        
        if not session:
            logger.warning(f"Invalid session: {session_id[:8]}...")
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Add user message to history
        current_app.session_manager.add_message(session_id, 'user', user_message)
        
        # TODO: Call RAG pipeline + Claude API
        # For now, return mock response
        ai_response = f"[MVP Mock] Ricevuto: '{user_message}'. RAG + Claude integration coming soon!"
        
        # Add assistant response to history
        current_app.session_manager.add_message(session_id, 'assistant', ai_response)
        
        # Record request for rate limiting
        if current_app.rate_limiter:
            current_app.rate_limiter.record_request(ip_address, session_id, 0.051)
        
        logger.info(f"Chat processed: {session_id[:8]}... (IP: {ip_address})")
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

@bp.route('/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """
    Get conversation history for session
    
    Returns:
        {
            'session_id': str,
            'messages': [
                {'role': str, 'content': str, 'timestamp': str}
            ]
        }
    """
    try:
        session = current_app.session_manager.get_session(session_id)
        
        if not session:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        history = current_app.session_manager.get_conversation_history(session_id)
        
        return jsonify({
            'session_id': session_id,
            'messages': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': 'Failed to get history'}), 500

@bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete session"""
    try:
        deleted = current_app.session_manager.delete_session(session_id)
        
        if deleted:
            return jsonify({'message': 'Session deleted'}), 200
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'error': 'Failed to delete session'}), 500
