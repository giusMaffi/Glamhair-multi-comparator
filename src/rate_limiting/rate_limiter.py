#!/usr/bin/env python3
"""
Rate Limiter for Glamhair Multi Comparator
Multi-layer rate limiting with cost protection

Author: Peppe
Date: 2026-01-22
"""

import time
import yaml
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Optional, List, Any
from threading import Lock
import hashlib

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rate_limiter')

# ============================================
# IN-MEMORY STORAGE (Development)
# ============================================

class InMemoryStorage:
    """In-memory storage backend with TTL support"""
    
    def __init__(self):
        self.store = {}
        self.expiry = {}
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[str]:
        """Get value with expiry check"""
        with self.lock:
            # Check expiry
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
                return None
            
            return self.store.get(key)
    
    def set(self, key: str, value: str, ttl: int):
        """Set value with TTL (seconds)"""
        with self.lock:
            self.store[key] = value
            self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def incr(self, key: str, ttl: int) -> int:
        """Increment counter with TTL"""
        with self.lock:
            # Check expiry
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
            
            # Increment
            current = int(self.store.get(key, 0))
            current += 1
            self.store[key] = str(current)
            
            # Set expiry if first increment
            if current == 1:
                self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
            
            return current
    
    def incr_float(self, key: str, amount: float, ttl: int):
        """Increment float value with TTL"""
        with self.lock:
            # Check expiry
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
            
            # Increment
            current = float(self.store.get(key, 0))
            current += amount
            self.store[key] = str(current)
            
            # Set expiry if first increment
            if current == amount:
                self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def exists(self, key: str) -> bool:
        """Check if key exists and not expired"""
        return self.get(key) is not None
    
    def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds"""
        with self.lock:
            if key not in self.expiry:
                return 0
            
            remaining = (self.expiry[key] - datetime.now()).total_seconds()
            return max(0, int(remaining))
    
    def sadd(self, key: str, value: str, ttl: int):
        """Add to set with TTL"""
        with self.lock:
            # Check expiry
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
            
            # Get or create set
            current_set = eval(self.store.get(key, '[]'))
            if value not in current_set:
                current_set.append(value)
            
            self.store[key] = str(current_set)
            self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def scard(self, key: str) -> int:
        """Get set cardinality"""
        with self.lock:
            # Check expiry
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
                return 0
            
            if key not in self.store:
                return 0
            
            return len(eval(self.store[key]))

# ============================================
# RATE LIMITER
# ============================================

class RateLimiter:
    """Multi-layer rate limiter with cost protection"""
    
    def __init__(self, config_path: str, use_redis: bool = False):
        """
        Initialize rate limiter
        
        Args:
            config_path: Path to rate_limits.yaml
            use_redis: Use Redis backend (not implemented yet)
        """
        self.config = self._load_config(config_path)
        
        # Storage backend
        if use_redis:
            # TODO: Implement Redis backend for production
            raise NotImplementedError("Redis backend not yet implemented")
        else:
            self.storage = InMemoryStorage()
        
        logger.info("✅ Rate limiter initialized (in-memory mode)")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"✅ Configuration loaded from {config_path}")
        return config
    
    def check_request(self, 
                     ip_address: str, 
                     session_id: str,
                     estimated_cost: float = 0.051) -> Dict[str, Any]:
        """
        Check if request is allowed
        
        Args:
            ip_address: Client IP address
            session_id: Session identifier
            estimated_cost: Estimated cost of this request
            
        Returns:
            {
                'allowed': bool,
                'throttled': bool,
                'delay': int (seconds),
                'reason': str,
                'retry_after': int (seconds),
                'message': str
            }
        """
        # Check whitelist
        if self._is_whitelisted(ip_address, session_id):
            return {'allowed': True, 'whitelisted': True}
        
        # Layer 1: IP rate limiting
        ip_check = self._check_ip_limits(ip_address)
        if not ip_check['allowed']:
            return ip_check
        
        # Layer 2: Session limits
        session_check = self._check_session_limits(session_id, ip_address)
        if not session_check['allowed']:
            return session_check
        
        # Layer 3: Global system limits
        global_check = self._check_global_limits(estimated_cost)
        if not global_check['allowed']:
            return global_check
        
        # All checks passed
        return {
            'allowed': True,
            'throttled': global_check.get('throttled', False),
            'delay': global_check.get('delay', 0),
        }
    
    def record_request(self, 
                      ip_address: str,
                      session_id: str,
                      cost: float):
        """
        Record a successful request
        
        Args:
            ip_address: Client IP address
            session_id: Session identifier
            cost: Actual cost of the request
        """
        today = date.today().isoformat()
        
        # Increment counters
        self.storage.incr(f"ip:{ip_address}:minute", ttl=60)
        self.storage.incr(f"ip:{ip_address}:hour", ttl=3600)
        self.storage.incr(f"ip:{ip_address}:day:{today}", ttl=86400)
        
        self.storage.incr(f"session:{session_id}:messages", ttl=1800)
        self.storage.incr(f"global:conversations:{today}", ttl=86400)
        
        # Track costs
        self.storage.incr_float(f"global:cost:{today}", cost, ttl=86400)
        
        # Track session start time (if new)
        session_key = f"session:{session_id}:start_time"
        if not self.storage.exists(session_key):
            self.storage.set(session_key, datetime.now().isoformat(), ttl=1800)
        
        # Add session to IP's daily sessions
        self.storage.sadd(f"ip:{ip_address}:sessions:{today}", session_id, ttl=86400)
    
    def _check_ip_limits(self, ip_address: str) -> Dict[str, Any]:
        """Check IP-based rate limits"""
        limits = self.config['ip_limits']
        today = date.today().isoformat()
        
        # Check minute limit
        minute_key = f"ip:{ip_address}:minute"
        minute_count = int(self.storage.get(minute_key) or 0)
        
        if minute_count >= limits['requests_per_minute']:
            retry_after = self.storage.ttl(minute_key)
            return {
                'allowed': False,
                'reason': 'rate_limit_minute',
                'retry_after': retry_after,
                'message': self.config['messages']['rate_limit_ip'].format(
                    retry_after=retry_after
                ),
            }
        
        # Check hour limit
        hour_key = f"ip:{ip_address}:hour"
        hour_count = int(self.storage.get(hour_key) or 0)
        
        if hour_count >= limits['requests_per_hour']:
            retry_after = self.storage.ttl(hour_key)
            return {
                'allowed': False,
                'reason': 'rate_limit_hour',
                'retry_after': retry_after // 60,
                'message': self.config['messages']['rate_limit_ip'].format(
                    retry_after=f"{retry_after // 60} minutes"
                ),
            }
        
        # Check day limit
        day_key = f"ip:{ip_address}:day:{today}"
        day_count = int(self.storage.get(day_key) or 0)
        
        if day_count >= limits['requests_per_day']:
            return {
                'allowed': False,
                'reason': 'rate_limit_day',
                'retry_after': self.storage.ttl(day_key),
                'message': self.config['messages']['daily_limit'],
            }
        
        return {'allowed': True}
    
    def _check_session_limits(self, session_id: str, ip_address: str) -> Dict[str, Any]:
        """Check session-based limits"""
        limits = self.config['session_limits']
        today = date.today().isoformat()
        
        # Check message count
        message_key = f"session:{session_id}:messages"
        message_count = int(self.storage.get(message_key) or 0)
        
        if message_count >= limits['max_messages']:
            return {
                'allowed': False,
                'reason': 'session_message_limit',
                'message': self.config['messages']['rate_limit_session'],
            }
        
        # Check session duration
        start_time_key = f"session:{session_id}:start_time"
        start_time_str = self.storage.get(start_time_key)
        
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            duration = datetime.now() - start_time
            max_duration = timedelta(minutes=limits['max_duration_minutes'])
            
            if duration > max_duration:
                return {
                    'allowed': False,
                    'reason': 'session_expired',
                    'message': self.config['messages']['session_expired'],
                }
        
        # Check daily sessions per IP
        sessions_key = f"ip:{ip_address}:sessions:{today}"
        daily_sessions = self.storage.scard(sessions_key)
        
        if daily_sessions >= limits['max_sessions_per_ip_per_day']:
            return {
                'allowed': False,
                'reason': 'daily_session_limit',
                'message': 'Daily session limit reached. Try again tomorrow.',
            }
        
        return {'allowed': True}
    
    def _check_global_limits(self, estimated_cost: float) -> Dict[str, Any]:
        """Check global system limits"""
        limits = self.config['global_limits']
        today = date.today().isoformat()
        
        # Check daily conversation count
        conv_key = f"global:conversations:{today}"
        daily_count = int(self.storage.get(conv_key) or 0)
        
        if daily_count >= limits['max_conversations_per_day']:
            self._send_alert('critical', 'traffic', 
                           f"Daily conversation limit reached: {daily_count}")
            return {
                'allowed': False,
                'reason': 'daily_capacity',
                'message': self.config['messages']['daily_limit'],
            }
        
        # Check daily cost
        cost_key = f"global:cost:{today}"
        daily_cost = float(self.storage.get(cost_key) or 0)
        daily_budget = limits['max_cost_per_day_usd']
        projected_cost = daily_cost + estimated_cost
        cost_ratio = projected_cost / daily_budget
        
        # Emergency stop (95%)
        if cost_ratio >= limits['emergency_stop']:
            self._send_alert('critical', 'cost',
                           f"Daily budget exceeded: ${daily_cost:.2f} / ${daily_budget:.2f}")
            return {
                'allowed': False,
                'reason': 'budget_exceeded',
                'message': self.config['messages']['budget_exceeded'],
            }
        
        # Throttle (90%)
        elif cost_ratio >= limits['throttle_threshold']:
            self._send_alert('warning', 'cost',
                           f"Daily budget at {cost_ratio*100:.0f}%: ${daily_cost:.2f} / ${daily_budget:.2f}")
            return {
                'allowed': True,
                'throttled': True,
                'delay': 5,  # Add 5 second delay
                'message': 'High demand. Response may be slower than usual.',
            }
        
        # Warning (80%)
        elif cost_ratio >= limits['warning_threshold']:
            self._send_alert('info', 'cost',
                           f"Daily budget at {cost_ratio*100:.0f}%: ${daily_cost:.2f} / ${daily_budget:.2f}")
        
        return {'allowed': True}
    
    def _is_whitelisted(self, ip_address: str, session_id: str) -> bool:
        """Check if IP or session is whitelisted"""
        whitelist = self.config.get('whitelist', {})
        return (
            ip_address in whitelist.get('ips', []) or
            session_id in whitelist.get('sessions', [])
        )
    
    def _send_alert(self, level: str, alert_type: str, message: str):
        """Send alert (logging only for now)"""
        log_level = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.CRITICAL
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"[{alert_type.upper()}] {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        today = date.today().isoformat()
        
        # Global stats
        daily_conversations = int(self.storage.get(f"global:conversations:{today}") or 0)
        daily_cost = float(self.storage.get(f"global:cost:{today}") or 0)
        
        limits = self.config['global_limits']
        
        return {
            'date': today,
            'conversations': {
                'count': daily_conversations,
                'limit': limits['max_conversations_per_day'],
                'percentage': (daily_conversations / limits['max_conversations_per_day'] * 100) if limits['max_conversations_per_day'] > 0 else 0,
            },
            'costs': {
                'today': daily_cost,
                'budget': limits['max_cost_per_day_usd'],
                'percentage': (daily_cost / limits['max_cost_per_day_usd'] * 100) if limits['max_cost_per_day_usd'] > 0 else 0,
            },
        }

# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == '__main__':
    """Test rate limiter"""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Initialize rate limiter
    config_path = project_root / 'config' / 'rate_limits.yaml'
    limiter = RateLimiter(str(config_path))
    
    print("=" * 60)
    print("🧪 RATE LIMITER TEST")
    print("=" * 60)
    
    # Test 1: Normal request
    print("\n📋 Test 1: Normal request")
    result = limiter.check_request("192.168.1.100", "session_123")
    print(f"Result: {result}")
    
    if result['allowed']:
        limiter.record_request("192.168.1.100", "session_123", 0.051)
        print("✅ Request recorded")
    
    # Test 2: Multiple requests (burst)
    print("\n📋 Test 2: Burst requests (testing per-minute limit)")
    for i in range(12):
        result = limiter.check_request("192.168.1.101", "session_456")
        if not result['allowed']:
            print(f"❌ Request {i+1}: Rate limited - {result['reason']}")
            break
        else:
            limiter.record_request("192.168.1.101", "session_456", 0.051)
            print(f"✅ Request {i+1}: Allowed")
    
    # Test 3: Status
    print("\n📋 Test 3: Get status")
    status = limiter.get_status()
    print(f"Status: {status}")
    
    print("\n" + "=" * 60)
    print("✅ RATE LIMITER TEST COMPLETE")
    print("=" * 60)