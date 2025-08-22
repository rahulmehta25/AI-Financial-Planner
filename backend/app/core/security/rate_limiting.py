"""
Rate Limiting Module

Implements rate limiting, DDoS protection, API throttling,
and brute force protection for the financial planning system.
"""

import time
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from collections import defaultdict, deque
import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimitType(Enum):
    """Types of rate limits"""
    API_CALL = "api_call"
    LOGIN_ATTEMPT = "login_attempt"
    DATA_EXPORT = "data_export"
    SIMULATION = "simulation"
    TRANSACTION = "transaction"
    PASSWORD_RESET = "password_reset"
    REGISTRATION = "registration"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    name: str
    limit_type: RateLimitType
    max_requests: int
    time_window: int  # seconds
    burst_size: Optional[int] = None
    penalty_duration: Optional[int] = None  # seconds for lockout
    applies_to: str = "ip"  # ip, user, api_key


@dataclass
class RateLimitViolation:
    """Rate limit violation record"""
    violator_id: str
    rule_name: str
    timestamp: datetime
    request_count: int
    limit: int
    blocked_until: Optional[datetime] = None


class TokenBucket:
    """
    Token bucket algorithm for rate limiting
    Allows burst traffic while maintaining average rate
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        
        # Refill bucket
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
        
        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """Calculate time until tokens are available"""
        
        if self.tokens >= tokens:
            return 0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class SlidingWindowCounter:
    """
    Sliding window counter for rate limiting
    More accurate than fixed windows
    """
    
    def __init__(self, window_size: int):
        self.window_size = window_size  # seconds
        self.requests = deque()
    
    def add_request(self) -> int:
        """Add a request and return current count"""
        
        now = time.time()
        
        # Remove old requests outside window
        cutoff = now - self.window_size
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        # Add new request
        self.requests.append(now)
        
        return len(self.requests)
    
    def get_count(self) -> int:
        """Get current request count in window"""
        
        now = time.time()
        cutoff = now - self.window_size
        
        # Remove old requests
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        return len(self.requests)


class RateLimiter:
    """
    Central rate limiting system
    """
    
    def __init__(self):
        self.redis_client = None
        self.rules = {}
        self.token_buckets = {}
        self.sliding_windows = {}
        self.violations = []
        self.load_rules()
    
    def load_rules(self):
        """Load rate limiting rules"""
        
        self.rules = {
            "api_general": RateLimitRule(
                name="api_general",
                limit_type=RateLimitType.API_CALL,
                max_requests=settings.RATE_LIMIT_PER_MINUTE,
                time_window=60,
                burst_size=10
            ),
            "api_hourly": RateLimitRule(
                name="api_hourly",
                limit_type=RateLimitType.API_CALL,
                max_requests=settings.RATE_LIMIT_PER_HOUR,
                time_window=3600
            ),
            "login": RateLimitRule(
                name="login",
                limit_type=RateLimitType.LOGIN_ATTEMPT,
                max_requests=5,
                time_window=300,  # 5 attempts per 5 minutes
                penalty_duration=1800  # 30 minute lockout
            ),
            "password_reset": RateLimitRule(
                name="password_reset",
                limit_type=RateLimitType.PASSWORD_RESET,
                max_requests=3,
                time_window=3600  # 3 per hour
            ),
            "registration": RateLimitRule(
                name="registration",
                limit_type=RateLimitType.REGISTRATION,
                max_requests=5,
                time_window=3600  # 5 per hour per IP
            ),
            "simulation": RateLimitRule(
                name="simulation",
                limit_type=RateLimitType.SIMULATION,
                max_requests=10,
                time_window=300,  # 10 simulations per 5 minutes
                applies_to="user"
            ),
            "data_export": RateLimitRule(
                name="data_export",
                limit_type=RateLimitType.DATA_EXPORT,
                max_requests=5,
                time_window=3600,  # 5 exports per hour
                applies_to="user"
            ),
            "transaction": RateLimitRule(
                name="transaction",
                limit_type=RateLimitType.TRANSACTION,
                max_requests=100,
                time_window=60,  # 100 transactions per minute
                burst_size=20,
                applies_to="user"
            )
        }
    
    async def initialize(self):
        """Initialize rate limiter"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def get_identifier(self, request: Request, rule: RateLimitRule, user_id: Optional[str] = None) -> str:
        """Get identifier for rate limiting"""
        
        if rule.applies_to == "user" and user_id:
            return f"user:{user_id}"
        elif rule.applies_to == "api_key":
            # Extract API key from request
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return f"api_key:{api_key}"
        
        # Default to IP address
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    async def check_rate_limit(
        self,
        request: Request,
        rule_name: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is within rate limits
        Returns (allowed, rate_limit_info)
        """
        
        if rule_name not in self.rules:
            return True, None
        
        rule = self.rules[rule_name]
        identifier = self.get_identifier(request, rule, user_id)
        
        # Check if identifier is blocked
        if await self.is_blocked(identifier, rule_name):
            blocked_until = await self.get_block_expiry(identifier, rule_name)
            return False, {
                "blocked": True,
                "blocked_until": blocked_until,
                "reason": "Rate limit exceeded"
            }
        
        # Use Redis for distributed rate limiting
        if self.redis_client:
            allowed = await self.check_redis_rate_limit(identifier, rule)
        else:
            # Fallback to local rate limiting
            allowed = self.check_local_rate_limit(identifier, rule)
        
        if not allowed:
            # Apply penalty if configured
            if rule.penalty_duration:
                await self.block_identifier(identifier, rule_name, rule.penalty_duration)
            
            # Record violation
            self.record_violation(identifier, rule)
            
            return False, {
                "limit": rule.max_requests,
                "window": rule.time_window,
                "retry_after": rule.time_window
            }
        
        return True, {
            "limit": rule.max_requests,
            "remaining": await self.get_remaining_requests(identifier, rule),
            "reset": await self.get_reset_time(identifier, rule)
        }
    
    async def check_redis_rate_limit(self, identifier: str, rule: RateLimitRule) -> bool:
        """Check rate limit using Redis"""
        
        key = f"rate_limit:{rule.name}:{identifier}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Increment counter
        pipe.incr(key)
        
        # Set expiry on first request
        pipe.expire(key, rule.time_window)
        
        # Get current count
        pipe.get(key)
        
        results = await pipe.execute()
        current_count = int(results[2] or 0)
        
        # Check burst size if configured
        if rule.burst_size:
            burst_key = f"{key}:burst"
            burst_count = await self.redis_client.incr(burst_key)
            
            if burst_count == 1:
                await self.redis_client.expire(burst_key, 1)  # 1 second burst window
            
            if burst_count > rule.burst_size:
                return False
        
        return current_count <= rule.max_requests
    
    def check_local_rate_limit(self, identifier: str, rule: RateLimitRule) -> bool:
        """Check rate limit using local memory"""
        
        key = f"{rule.name}:{identifier}"
        
        # Use sliding window counter
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindowCounter(rule.time_window)
        
        counter = self.sliding_windows[key]
        current_count = counter.add_request()
        
        # Check burst size using token bucket
        if rule.burst_size:
            bucket_key = f"{key}:bucket"
            if bucket_key not in self.token_buckets:
                refill_rate = rule.max_requests / rule.time_window
                self.token_buckets[bucket_key] = TokenBucket(rule.burst_size, refill_rate)
            
            bucket = self.token_buckets[bucket_key]
            if not bucket.consume():
                return False
        
        return current_count <= rule.max_requests
    
    async def is_blocked(self, identifier: str, rule_name: str) -> bool:
        """Check if identifier is blocked"""
        
        if self.redis_client:
            block_key = f"blocked:{rule_name}:{identifier}"
            return await self.redis_client.exists(block_key)
        
        return False
    
    async def get_block_expiry(self, identifier: str, rule_name: str) -> Optional[datetime]:
        """Get block expiry time"""
        
        if self.redis_client:
            block_key = f"blocked:{rule_name}:{identifier}"
            ttl = await self.redis_client.ttl(block_key)
            
            if ttl > 0:
                return datetime.utcnow() + timedelta(seconds=ttl)
        
        return None
    
    async def block_identifier(self, identifier: str, rule_name: str, duration: int):
        """Block an identifier for specified duration"""
        
        if self.redis_client:
            block_key = f"blocked:{rule_name}:{identifier}"
            await self.redis_client.setex(block_key, duration, "blocked")
    
    async def get_remaining_requests(self, identifier: str, rule: RateLimitRule) -> int:
        """Get remaining requests in current window"""
        
        if self.redis_client:
            key = f"rate_limit:{rule.name}:{identifier}"
            current = await self.redis_client.get(key)
            
            if current:
                return max(0, rule.max_requests - int(current))
        
        return rule.max_requests
    
    async def get_reset_time(self, identifier: str, rule: RateLimitRule) -> datetime:
        """Get time when rate limit resets"""
        
        if self.redis_client:
            key = f"rate_limit:{rule.name}:{identifier}"
            ttl = await self.redis_client.ttl(key)
            
            if ttl > 0:
                return datetime.utcnow() + timedelta(seconds=ttl)
        
        return datetime.utcnow() + timedelta(seconds=rule.time_window)
    
    def record_violation(self, identifier: str, rule: RateLimitRule):
        """Record rate limit violation"""
        
        violation = RateLimitViolation(
            violator_id=identifier,
            rule_name=rule.name,
            timestamp=datetime.utcnow(),
            request_count=rule.max_requests + 1,
            limit=rule.max_requests
        )
        
        self.violations.append(violation)
    
    async def reset_limits(self, identifier: str, rule_name: Optional[str] = None):
        """Reset rate limits for identifier"""
        
        if self.redis_client:
            if rule_name:
                keys = [f"rate_limit:{rule_name}:{identifier}"]
            else:
                # Reset all rules for identifier
                keys = []
                for rule in self.rules:
                    keys.append(f"rate_limit:{rule}:{identifier}")
            
            if keys:
                await self.redis_client.delete(*keys)


class DDoSProtection:
    """
    DDoS protection system
    """
    
    def __init__(self):
        self.redis_client = None
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.request_patterns = defaultdict(list)
        self.threat_scores = {}
    
    async def initialize(self):
        """Initialize DDoS protection"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def analyze_request(self, request: Request) -> Tuple[bool, Optional[str]]:
        """
        Analyze request for DDoS patterns
        Returns (allowed, reason_if_blocked)
        """
        
        client_ip = request.client.host
        
        # Check if IP is blocked
        if await self.is_ip_blocked(client_ip):
            return False, "IP address blocked due to suspicious activity"
        
        # Calculate threat score
        threat_score = await self.calculate_threat_score(request)
        
        # Update threat score
        self.threat_scores[client_ip] = threat_score
        
        # Block if threat score exceeds threshold
        if threat_score > 80:
            await self.block_ip(client_ip, 3600)  # Block for 1 hour
            return False, f"Threat score too high: {threat_score}"
        
        # Add to suspicious list if moderately high
        if threat_score > 50:
            self.suspicious_ips.add(client_ip)
        
        # Check for attack patterns
        if await self.detect_attack_pattern(request):
            await self.block_ip(client_ip, 1800)  # Block for 30 minutes
            return False, "Attack pattern detected"
        
        return True, None
    
    async def calculate_threat_score(self, request: Request) -> int:
        """Calculate threat score for request"""
        
        score = 0
        client_ip = request.client.host
        
        # Check request rate
        rate = await self.get_request_rate(client_ip)
        if rate > 100:  # More than 100 requests per minute
            score += min(50, rate // 2)
        
        # Check for suspicious headers
        if self.has_suspicious_headers(request):
            score += 20
        
        # Check for known attack patterns in URL
        if self.has_attack_pattern_in_url(request.url.path):
            score += 30
        
        # Check if IP is in suspicious list
        if client_ip in self.suspicious_ips:
            score += 10
        
        # Check geographic anomalies
        if await self.has_geographic_anomaly(client_ip):
            score += 15
        
        # Check for bot patterns
        if self.is_likely_bot(request):
            score += 25
        
        return min(100, score)
    
    async def get_request_rate(self, ip: str) -> int:
        """Get request rate for IP"""
        
        if self.redis_client:
            key = f"request_rate:{ip}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        
        return 0
    
    def has_suspicious_headers(self, request: Request) -> bool:
        """Check for suspicious headers"""
        
        headers = request.headers
        
        # Check for missing common headers
        if not headers.get("user-agent"):
            return True
        
        # Check for suspicious user agents
        suspicious_agents = ["scanner", "bot", "crawler", "scraper", "hack"]
        user_agent = headers.get("user-agent", "").lower()
        
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Check for header anomalies
        if headers.get("x-forwarded-for") and len(headers.get("x-forwarded-for", "").split(",")) > 5:
            return True
        
        return False
    
    def has_attack_pattern_in_url(self, path: str) -> bool:
        """Check for attack patterns in URL"""
        
        attack_patterns = [
            "../",  # Path traversal
            "<script",  # XSS attempt
            "union select",  # SQL injection
            "exec(",  # Command injection
            "${",  # Template injection
            "%00",  # Null byte injection
            "../../etc/passwd",  # Specific file access
            ".env",  # Environment file access
            "wp-admin",  # WordPress admin (if not WordPress site)
            "phpmyadmin"  # Database admin
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in attack_patterns)
    
    async def has_geographic_anomaly(self, ip: str) -> bool:
        """Check for geographic anomalies"""
        
        # This would use a GeoIP service in production
        # For now, check if IP is from known problematic ranges
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Check if it's from private/reserved ranges
            if ip_obj.is_private or ip_obj.is_reserved:
                return True
            
        except ValueError:
            return True
        
        return False
    
    def is_likely_bot(self, request: Request) -> bool:
        """Check if request is likely from a bot"""
        
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Known bot signatures
        bot_signatures = [
            "bot", "crawler", "spider", "scraper",
            "wget", "curl", "python", "java",
            "go-http-client", "postman"
        ]
        
        # Check user agent
        if any(sig in user_agent for sig in bot_signatures):
            # Allow known good bots
            good_bots = ["googlebot", "bingbot", "slackbot"]
            if not any(bot in user_agent for bot in good_bots):
                return True
        
        # Check for browser impersonation
        if "mozilla" in user_agent and "chrome" in user_agent:
            # Check for missing browser-specific headers
            if not request.headers.get("sec-fetch-dest"):
                return True
        
        return False
    
    async def detect_attack_pattern(self, request: Request) -> bool:
        """Detect coordinated attack patterns"""
        
        client_ip = request.client.host
        current_time = time.time()
        
        # Track request pattern
        pattern_key = f"{request.method}:{request.url.path}"
        self.request_patterns[client_ip].append((current_time, pattern_key))
        
        # Clean old entries
        cutoff = current_time - 60  # 1 minute window
        self.request_patterns[client_ip] = [
            (t, p) for t, p in self.request_patterns[client_ip]
            if t > cutoff
        ]
        
        patterns = self.request_patterns[client_ip]
        
        # Check for pattern anomalies
        if len(patterns) > 50:  # More than 50 requests per minute
            # Check if all requests are identical
            unique_patterns = set(p for _, p in patterns)
            if len(unique_patterns) == 1:
                return True  # Same request repeated
            
            # Check if requests are too regular (bot-like)
            if len(patterns) > 10:
                intervals = [patterns[i][0] - patterns[i-1][0] for i in range(1, len(patterns))]
                avg_interval = sum(intervals) / len(intervals)
                
                # Check if intervals are too consistent
                variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
                if variance < 0.1:  # Very regular intervals
                    return True
        
        return False
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        
        if ip in self.blocked_ips:
            return True
        
        if self.redis_client:
            block_key = f"ddos_block:{ip}"
            return await self.redis_client.exists(block_key)
        
        return False
    
    async def block_ip(self, ip: str, duration: int):
        """Block an IP address"""
        
        self.blocked_ips.add(ip)
        
        if self.redis_client:
            block_key = f"ddos_block:{ip}"
            await self.redis_client.setex(block_key, duration, "blocked")
    
    async def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        
        self.blocked_ips.discard(ip)
        
        if self.redis_client:
            block_key = f"ddos_block:{ip}"
            await self.redis_client.delete(block_key)


class APIThrottler:
    """
    API throttling for expensive operations
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.operation_costs = {}
        self.load_operation_costs()
    
    def load_operation_costs(self):
        """Load operation costs for throttling"""
        
        self.operation_costs = {
            "simulation": 10,  # High cost
            "portfolio_optimization": 8,
            "data_export": 5,
            "report_generation": 5,
            "bulk_update": 7,
            "market_data_fetch": 3,
            "standard_api": 1  # Low cost
        }
    
    async def check_throttle(
        self,
        operation: str,
        request: Request,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if operation should be throttled"""
        
        cost = self.operation_costs.get(operation, 1)
        
        # Adjust rate limit based on cost
        if cost > 5:
            # Use stricter limits for expensive operations
            return await self.rate_limiter.check_rate_limit(
                request,
                "simulation",
                user_id
            )
        else:
            # Use standard API limits
            return await self.rate_limiter.check_rate_limit(
                request,
                "api_general",
                user_id
            )


class BruteForceProtection:
    """
    Brute force attack protection
    """
    
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.locked_accounts = {}
        self.redis_client = None
    
    async def initialize(self):
        """Initialize brute force protection"""
        
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def record_failed_attempt(
        self,
        identifier: str,
        attempt_type: str = "login"
    ):
        """Record a failed attempt"""
        
        if self.redis_client:
            key = f"failed_attempts:{attempt_type}:{identifier}"
            
            # Increment counter
            count = await self.redis_client.incr(key)
            
            # Set expiry on first attempt
            if count == 1:
                await self.redis_client.expire(key, 3600)  # 1 hour window
            
            # Check thresholds
            if count >= 5:
                await self.lock_account(identifier, attempt_type)
        else:
            # Local tracking
            self.failed_attempts[identifier].append(time.time())
            
            # Clean old attempts
            cutoff = time.time() - 3600
            self.failed_attempts[identifier] = [
                t for t in self.failed_attempts[identifier]
                if t > cutoff
            ]
            
            if len(self.failed_attempts[identifier]) >= 5:
                await self.lock_account(identifier, attempt_type)
    
    async def record_successful_attempt(
        self,
        identifier: str,
        attempt_type: str = "login"
    ):
        """Record a successful attempt and reset counter"""
        
        if self.redis_client:
            key = f"failed_attempts:{attempt_type}:{identifier}"
            await self.redis_client.delete(key)
        else:
            self.failed_attempts[identifier] = []
    
    async def lock_account(
        self,
        identifier: str,
        attempt_type: str,
        duration: int = 1800  # 30 minutes
    ):
        """Lock an account due to too many failed attempts"""
        
        if self.redis_client:
            lock_key = f"account_lock:{attempt_type}:{identifier}"
            await self.redis_client.setex(lock_key, duration, "locked")
        else:
            self.locked_accounts[identifier] = time.time() + duration
    
    async def is_locked(
        self,
        identifier: str,
        attempt_type: str = "login"
    ) -> bool:
        """Check if account is locked"""
        
        if self.redis_client:
            lock_key = f"account_lock:{attempt_type}:{identifier}"
            return await self.redis_client.exists(lock_key)
        else:
            if identifier in self.locked_accounts:
                if self.locked_accounts[identifier] > time.time():
                    return True
                else:
                    del self.locked_accounts[identifier]
            return False
    
    async def unlock_account(
        self,
        identifier: str,
        attempt_type: str = "login"
    ):
        """Manually unlock an account"""
        
        if self.redis_client:
            lock_key = f"account_lock:{attempt_type}:{identifier}"
            await self.redis_client.delete(lock_key)
        else:
            self.locked_accounts.pop(identifier, None)