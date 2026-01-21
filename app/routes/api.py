#!/usr/bin/env python3
"""
API Routes - Claude Integration
Chat endpoints for Glamhair Multi Comparator

Author: Peppe
Date: 2026-01-21
Version: 2.0 - Claude Integration
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from src.rag.retriever import get_retriever, format_products_for_context
from src.api.claude_client import get_claude_client

logger = logging.getLogger('api_routes')

bp = Blueprint('api', __name__, url_prefix='/api')

def get_client_ip():
    """Get client IP address (handles proxies)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

@bp.route('/session/start', methods=['POST'])
def start_session():
    """Start new conversation session"""
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
    """Send message and get AI response"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        user_message = data.get('message')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        if not user_message:
            return jsonify({'error': 'message required'}), 400
        
        ip_address = get_client_ip()
        
        if current_app.rate_limiter:
            rate_check = current_app.rate_limiter.check_request(
                ip_address, 
                session_id,
                estimated_cost=0.051
            )
            
            if not rate_check['allowed']:
                logger.warning(f"Rate limit exceeded: {ip_address}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'reason': rate_check['reason'],
                    'message': rate_check.get('message', 'Too many requests'),
                    'retry_after': rate_check.get('retry_after', 60)
                }), 429
        
        session = current_app.session_manager.get_session(session_id)
        
        if not session:
            logger.warning(f"Invalid session: {session_id[:8]}...")
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        current_app.session_manager.add_message(session_id, 'user', user_message)
        
        # RAG PIPELINE + CLAUDE
        try:
            retriever = get_retriever()
            
            logger.info(f"Searching products for: '{user_message[:100]}'")
            products = retriever.search(
                query=user_message,
                top_k=20,
                min_similarity=0.3
            )
            
            logger.info(f"Found {len(products)} relevant products")
            
            products_context = format_products_for_context(products, max_products=20)
            
            conversation_history = current_app.session_manager.get_conversation_history(session_id)
            if conversation_history and len(conversation_history) > 0:
                conversation_history = conversation_history[:-1]
            
            claude_history = [
                {'role': msg['role'], 'content': msg['content']}
                for msg in conversation_history
            ]
            
            claude_client = get_claude_client()
            
            logger.info("Calling Claude API...")
            ai_response, claude_metadata = claude_client.get_response(
                user_message=user_message,
                conversation_history=claude_history,
                products_context=products_context
            )
            
            if not claude_metadata.get('success', False):
                logger.error(f"Claude failed: {claude_metadata.get('error_message')}")
                ai_response = (
                    "Mi dispiace, si è verificato un problema tecnico. "
                    "Riprova tra qualche secondo."
                )
                actual_cost = 0.0
            else:
                actual_cost = claude_metadata.get('cost_usd', 0.051)
                logger.info(
                    f"Claude response: "
                    f"{claude_metadata.get('total_tokens')} tokens, "
                    f"${actual_cost:.4f}"
                )
            
        except Exception as e:
            logger.error(f"Error in RAG/Claude pipeline: {e}", exc_info=True)
            ai_response = (
                "Mi dispiace, si è verificato un errore. Riprova."
            )
            products = []
            claude_metadata = {'success': False, 'error_message': str(e)}
            actual_cost = 0.0
        
        current_app.session_manager.add_message(session_id, 'assistant', ai_response)
        
        if current_app.rate_limiter:
            current_app.rate_limiter.record_request(ip_address, session_id, actual_cost)
        
        logger.info(f"Chat processed: {session_id[:8]}...")
        
        response_metadata = {
            'products_retrieved': len(products),
        }
        
        if claude_metadata.get('success', False):
            response_metadata.update({
                'tokens_used': claude_metadata.get('total_tokens', 0),
                'cost_usd': claude_metadata.get('cost_usd', 0.0),
                'model': claude_metadata.get('model', 'unknown'),
            })
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id,
            'metadata': response_metadata
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        return jsonify({'error': 'Failed to process message'}), 500

@bp.route('/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """Get conversation history for session"""
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

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        stats = {}
        
        try:
            retriever = get_retriever()
            stats['retriever'] = retriever.get_stats()
        except Exception as e:
            stats['retriever'] = {'error': str(e)}
        
        try:
            claude_client = get_claude_client()
            stats['claude_client'] = claude_client.get_stats()
        except Exception as e:
            stats['claude_client'] = {'error': str(e)}
        
        if current_app.rate_limiter:
            try:
                stats['rate_limiter'] = current_app.rate_limiter.get_stats()
            except Exception as e:
                stats['rate_limiter'] = {'error': str(e)}
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500