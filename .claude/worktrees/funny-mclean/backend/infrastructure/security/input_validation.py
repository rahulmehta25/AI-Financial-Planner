"""
Input Validation and Sanitization

Comprehensive input validation to prevent injection attacks and data corruption.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation
import bleach
from sqlalchemy import text
from sqlalchemy.engine import Engine
import validators


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|FROM|WHERE|ORDER BY|GROUP BY|HAVING)\b)",
        r"(--|#|\/\*|\*\/|;|\||&&|\|\||xp_|sp_|0x)",
        r"(\bOR\b\s*\d+\s*=\s*\d+)",
        r"(\bAND\b\s*\d+\s*=\s*\d+)",
        r"(SLEEP\s*\(|BENCHMARK\s*\(|WAITFOR\s+DELAY)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<applet[^>]*>.*?</applet>",
        r"<form[^>]*>.*?</form>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
        r"vbscript:",
        r"data:text/html",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\/",
        r"%2e%2e%2f",
        r"%252e%252e%252f",
        r"\.\.%2f",
        r"\.\.%5c",
        r"/etc/passwd",
        r"C:\\\\Windows",
        r"../../",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`.*`",
        r"\|.*\|",
        r"&&",
        r"\|\|",
        r">",
        r"<",
        r">>",
        r"<<",
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email address format"""
        if not email or len(email) > 254:
            return False
        return validators.email(email)
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        # Check if it's a valid phone number (10-15 digits)
        return bool(re.match(r'^\d{10,15}$', cleaned))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format and protocol"""
        if not url:
            return False
        
        # Check for valid URL
        result = validators.url(url)
        if not result:
            return False
        
        # Only allow http/https protocols
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ['http', 'https']
    
    @classmethod
    def sanitize_html(cls, html_content: str, allowed_tags: Optional[List[str]] = None) -> str:
        """Sanitize HTML content to prevent XSS"""
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
        
        allowed_attributes = {
            'a': ['href', 'title'],
        }
        
        # Clean HTML using bleach
        cleaned = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        return cleaned
    
    @classmethod
    def sanitize_string(cls, input_string: str, max_length: int = 1000) -> str:
        """Basic string sanitization"""
        if not input_string:
            return ""
        
        # Truncate to max length
        sanitized = input_string[:max_length]
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char == '\n' or char == '\t')
        
        return sanitized.strip()
    
    @classmethod
    def check_sql_injection(cls, input_string: str) -> bool:
        """Check for potential SQL injection patterns"""
        if not input_string:
            return False
        
        input_upper = input_string.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_xss(cls, input_string: str) -> bool:
        """Check for potential XSS patterns"""
        if not input_string:
            return False
        
        input_lower = input_string.lower()
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_path_traversal(cls, path: str) -> bool:
        """Check for path traversal attempts"""
        if not path:
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_command_injection(cls, command: str) -> bool:
        """Check for command injection attempts"""
        if not command:
            return False
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, command):
                return True
        
        return False
    
    @classmethod
    def validate_numeric(cls, value: Any, min_value: Optional[float] = None, 
                        max_value: Optional[float] = None) -> Optional[float]:
        """Validate and convert numeric input"""
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                return None
            
            if max_value is not None and num_value > max_value:
                return None
            
            return num_value
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def validate_decimal(cls, value: Any, max_digits: int = 10, 
                        decimal_places: int = 2) -> Optional[Decimal]:
        """Validate decimal/currency values"""
        try:
            decimal_value = Decimal(str(value))
            
            # Check total digits and decimal places
            sign, digits, exponent = decimal_value.as_tuple()
            
            if len(digits) > max_digits:
                return None
            
            if abs(exponent) > decimal_places:
                # Round to specified decimal places
                decimal_value = decimal_value.quantize(
                    Decimal(10) ** -decimal_places
                )
            
            return decimal_value
        except (InvalidOperation, ValueError, TypeError):
            return None
    
    @classmethod
    def validate_date(cls, date_string: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
        """Validate date string"""
        try:
            return datetime.strptime(date_string, format)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def validate_json_payload(cls, payload: Dict[str, Any], 
                             required_fields: List[str]) -> tuple[bool, List[str]]:
        """Validate JSON payload structure"""
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        
        # Check for suspicious patterns in values
        for key, value in payload.items():
            if isinstance(value, str):
                if cls.check_sql_injection(value):
                    errors.append(f"Potential SQL injection in field: {key}")
                if cls.check_xss(value):
                    errors.append(f"Potential XSS in field: {key}")
            elif isinstance(value, dict):
                # Recursive validation for nested objects
                nested_valid, nested_errors = cls.validate_json_payload(value, [])
                if not nested_valid:
                    errors.extend([f"{key}.{err}" for err in nested_errors])
        
        return len(errors) == 0, errors
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove path components
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Limit length
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            return f"{name[:200]}.{ext[:10]}"
        return filename[:210]


class SQLParameterizer:
    """Safe SQL query construction with parameterization"""
    
    @staticmethod
    def build_safe_query(base_query: str, filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build parameterized SQL query"""
        conditions = []
        params = {}
        
        for key, value in filters.items():
            # Sanitize column name (whitelist approach)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f"Invalid column name: {key}")
            
            param_name = f"param_{key}"
            conditions.append(f"{key} = :{param_name}")
            params[param_name] = value
        
        if conditions:
            query = f"{base_query} WHERE {' AND '.join(conditions)}"
        else:
            query = base_query
        
        return query, params
    
    @staticmethod
    def execute_safe_query(engine: Engine, query: str, params: Dict[str, Any]):
        """Execute parameterized query safely"""
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            return result.fetchall()


class CSRFProtection:
    """CSRF token generation and validation"""
    
    import secrets
    import hmac
    import hashlib
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = self.secrets.token_urlsafe(32)
        signature = self._sign_token(token, session_id)
        return f"{token}.{signature}"
    
    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        try:
            token_part, signature = token.rsplit('.', 1)
            expected_signature = self._sign_token(token_part, session_id)
            return self.hmac.compare_digest(signature, expected_signature)
        except ValueError:
            return False
    
    def _sign_token(self, token: str, session_id: str) -> str:
        """Sign token with HMAC"""
        message = f"{token}.{session_id}".encode()
        signature = self.hmac.new(
            self.secret_key.encode(),
            message,
            self.hashlib.sha256
        ).hexdigest()
        return signature


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, window)
        
        return current <= limit
    
    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests in current window"""
        current = await self.redis.get(key)
        if current is None:
            return limit
        return max(0, limit - int(current))