#!/usr/bin/env python3
"""
Conversation Manager for Glamhair Multi Comparator
Manages conversation history formatting for Claude API

Author: Peppe
Date: 2026-01-21
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

ROLE_USER = 'user'
ROLE_ASSISTANT = 'assistant'

MAX_CONVERSATION_TOKENS = 150_000
CHARS_PER_TOKEN = 4

class ConversationManager:
    """Manages conversation history for Claude API"""
    
    def __init__(self, max_tokens: int = MAX_CONVERSATION_TOKENS):
        self.max_tokens = max_tokens
        logger.info(f"ConversationManager initialized (max_tokens={max_tokens})")
    
    def format_for_claude(
        self,
        conversation_history: List[Dict] = None,
        new_user_message: str = None
    ) -> List[Dict]:
        """Format conversation history for Claude API"""
        messages = []
        
        if conversation_history:
            for msg in conversation_history:
                if self._validate_message(msg):
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        
        if new_user_message:
            messages.append({
                'role': ROLE_USER,
                'content': new_user_message
            })
        
        messages = self._ensure_alternating_roles(messages)
        messages = self._truncate_to_limit(messages)
        
        logger.info(f"Formatted {len(messages)} messages for Claude")
        return messages
    
    def _validate_message(self, message: Dict) -> bool:
        """Validate message format"""
        if not isinstance(message, dict):
            return False
        
        if 'role' not in message or 'content' not in message:
            return False
        
        if message['role'] not in [ROLE_USER, ROLE_ASSISTANT]:
            return False
        
        if not isinstance(message['content'], str):
            return False
        
        if not message['content'].strip():
            return False
        
        return True
    
    def _ensure_alternating_roles(self, messages: List[Dict]) -> List[Dict]:
        """Ensure messages alternate between user and assistant"""
        if not messages:
            return messages
        
        if messages[0]['role'] != ROLE_USER:
            while messages and messages[0]['role'] != ROLE_USER:
                messages.pop(0)
        
        cleaned_messages = []
        last_role = None
        
        for msg in messages:
            if msg['role'] != last_role:
                cleaned_messages.append(msg)
                last_role = msg['role']
        
        return cleaned_messages
    
    def _truncate_to_limit(self, messages: List[Dict]) -> List[Dict]:
        """Truncate conversation to stay within token limit"""
        if not messages:
            return messages
        
        total_chars = sum(len(msg['content']) for msg in messages)
        estimated_tokens = total_chars // CHARS_PER_TOKEN
        
        if estimated_tokens <= self.max_tokens:
            return messages
        
        logger.info(f"Truncating conversation ({estimated_tokens} > {self.max_tokens})")
        
        truncated_messages = []
        current_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = len(msg['content']) // CHARS_PER_TOKEN
            
            if current_tokens + msg_tokens <= self.max_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        truncated_messages = self._ensure_alternating_roles(truncated_messages)
        
        logger.info(f"Truncated to {len(truncated_messages)} messages (~{current_tokens} tokens)")
        
        return truncated_messages
