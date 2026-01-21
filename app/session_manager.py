#!/usr/bin/env python3
"""
Session Manager
Handles user sessions and conversation history

Author: Peppe
Date: 2026-01-22
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock

# ============================================
# LOGGING
# ============================================

logger = logging.getLogger('session_manager')

# ============================================
# SESSION MANAGER
# ============================================

class SessionManager:
    """Manages user sessions and conversation history"""
    
    def __init__(self, session_lifetime_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            session_lifetime_minutes: Session lifetime in minutes
        """
        self.sessions = {}  # session_id -> session_data
        self.session_lifetime = timedelta(minutes=session_lifetime_minutes)
        self.lock = Lock()
        
        logger.info(f"✅ Session manager initialized (lifetime: {session_lifetime_minutes} min)")
    
    def create_session(self, ip_address: str) -> str:
        """
        Create new session
        
        Args:
            ip_address: Client IP address
            
        Returns:
            session_id: New session ID
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            
            self.sessions[session_id] = {
                'id': session_id,
                'ip_address': ip_address,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'messages': [],
                'metadata': {}
            }
            
            logger.info(f"✅ New session created: {session_id[:8]}... (IP: {ip_address})")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found/expired
        """
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(f"Session not found: {session_id[:8]}...")
                return None
            
            session = self.sessions[session_id]
            
            # Check expiry
            if self._is_expired(session):
                logger.info(f"Session expired: {session_id[:8]}...")
                del self.sessions[session_id]
                return None
            
            # Update last activity
            session['last_activity'] = datetime.now()
            
            return session
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add message to conversation history
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.error(f"Cannot add message: session not found {session_id[:8]}...")
                return False
            
            if self._is_expired(session):
                logger.warning(f"Cannot add message: session expired {session_id[:8]}...")
                del self.sessions[session_id]
                return False
            
            # Add message
            session['messages'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            
            session['last_activity'] = datetime.now()
            
            logger.debug(f"Message added to session {session_id[:8]}... (role: {role})")
            return True
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        session = self.get_session(session_id)
        
        if not session:
            return []
        
        return session['messages']
    
    def update_metadata(self, session_id: str, key: str, value: Any) -> bool:
        """
        Update session metadata
        
        Args:
            session_id: Session ID
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if successful
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return False
            
            session['metadata'][key] = value
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session deleted: {session_id[:8]}...")
                return True
            
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions removed
        """
        with self.lock:
            expired = [
                sid for sid, session in self.sessions.items()
                if self._is_expired(session)
            ]
            
            for sid in expired:
                del self.sessions[sid]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
            
            return len(expired)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        with self.lock:
            return len(self.sessions)
    
    def _is_expired(self, session: Dict) -> bool:
        """Check if session is expired"""
        last_activity = session['last_activity']
        return datetime.now() - last_activity > self.session_lifetime