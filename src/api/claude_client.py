#!/usr/bin/env python3
"""
Claude API Client for Glamhair Multi Comparator
Handles Anthropic API calls with conversation history management

Author: Peppe
Date: 2026-01-21
"""

import logging
import time
from typing import List, Dict, Tuple
import anthropic

from src.config import (
    ANTHROPIC_API_KEY,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    MAX_TOKENS,
)

from src.api.prompts.base_prompt import get_system_prompt
from src.api.prompts.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

class ClaudeClient:
    """Client for Anthropic Claude API"""
    
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_manager = ConversationManager()
        
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost_usd': 0.0,
        }
        
        logger.info(f"ClaudeClient initialized with model: {MODEL_NAME}")
    
    def get_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        products_context: str = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> Tuple[str, Dict]:
        """Get response from Claude"""
        if max_tokens is None:
            max_tokens = MAX_TOKENS
        
        if temperature is None:
            temperature = MODEL_TEMPERATURE
        
        try:
            logger.info(f"Getting Claude response for: '{user_message[:100]}...'")
            start_time = time.time()
            
            system_prompt = get_system_prompt(products_context=products_context)
            
            messages = self.conversation_manager.format_for_claude(
                conversation_history=conversation_history,
                new_user_message=user_message
            )
            
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            response_text = response.content[0].text
            
            elapsed_time = time.time() - start_time
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            
            cost_usd = self._calculate_cost(input_tokens, output_tokens)
            
            self.stats['total_calls'] += 1
            self.stats['successful_calls'] += 1
            self.stats['total_input_tokens'] += input_tokens
            self.stats['total_output_tokens'] += output_tokens
            self.stats['total_cost_usd'] += cost_usd
            
            metadata = {
                'success': True,
                'model': MODEL_NAME,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost_usd': cost_usd,
                'elapsed_time': elapsed_time,
                'stop_reason': response.stop_reason,
            }
            
            logger.info(
                f"✅ Claude response received "
                f"({input_tokens} in / {output_tokens} out / "
                f"${cost_usd:.4f} / {elapsed_time:.2f}s)"
            )
            
            return response_text, metadata
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            self.stats['total_calls'] += 1
            self.stats['failed_calls'] += 1
            
            metadata = {
                'success': False,
                'error_type': 'api_error',
                'error_message': str(e),
            }
            
            return self._get_error_response(e), metadata
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.stats['total_calls'] += 1
            self.stats['failed_calls'] += 1
            
            metadata = {
                'success': False,
                'error_type': 'unknown_error',
                'error_message': str(e),
            }
            
            return self._get_error_response(e), metadata
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost (Claude Sonnet 4: $3/1M input, $15/1M output)"""
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        return input_cost + output_cost
    
    def _get_error_response(self, error: Exception) -> str:
        """Get user-friendly error message"""
        if isinstance(error, anthropic.RateLimitError):
            return (
                "Mi dispiace, stiamo ricevendo troppe richieste. "
                "Riprova tra qualche secondo."
            )
        elif isinstance(error, anthropic.APIConnectionError):
            return (
                "C'è un problema di connessione con il servizio AI. "
                "Verifica la tua connessione e riprova."
            )
        elif isinstance(error, anthropic.AuthenticationError):
            return (
                "Errore di autenticazione. "
                "Contatta l'amministratore."
            )
        else:
            return (
                "Si è verificato un errore imprevisto. "
                "Riprova o contatta l'assistenza."
            )
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        stats = self.stats.copy()
        
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
            stats['avg_input_tokens'] = stats['total_input_tokens'] / stats['total_calls']
            stats['avg_output_tokens'] = stats['total_output_tokens'] / stats['total_calls']
            stats['avg_cost_per_call'] = stats['total_cost_usd'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
            stats['avg_input_tokens'] = 0
            stats['avg_output_tokens'] = 0
            stats['avg_cost_per_call'] = 0.0
        
        return stats

_client_instance = None

def get_claude_client() -> ClaudeClient:
    """Get or create global Claude client instance"""
    global _client_instance
    
    if _client_instance is None:
        logger.info("Creating Claude client instance...")
        _client_instance = ClaudeClient()
    
    return _client_instance
