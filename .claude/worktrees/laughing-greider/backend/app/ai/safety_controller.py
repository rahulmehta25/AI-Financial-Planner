"""Safety controller for AI narrative generation."""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path


class SafetyViolationType(str, Enum):
    """Types of safety violations."""
    PROHIBITED_CONTENT = "prohibited_content"
    NUMERICAL_INCONSISTENCY = "numerical_inconsistency"
    MISSING_DISCLAIMER = "missing_disclaimer"
    TEMPLATE_VIOLATION = "template_violation"
    PROMPT_INJECTION = "prompt_injection"
    PII_DETECTED = "pii_detected"
    ADVICE_VIOLATION = "advice_violation"


class SafetyController:
    """Controls safety and compliance for AI narratives."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize safety controller.
        
        Args:
            config: Safety configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize safety rules
        self._initialize_safety_rules()
        
        # Initialize disclaimers
        self._initialize_disclaimers()
        
        # Track violations for reporting
        self.violation_history: List[Dict[str, Any]] = []
    
    def _initialize_safety_rules(self):
        """Initialize safety validation rules."""
        # Prohibited terms that suggest specific financial advice
        self.prohibited_terms = [
            "guaranteed return",
            "risk-free",
            "can't lose",
            "sure thing",
            "insider information",
            "hot tip",
            "get rich quick",
            "double your money",
            "act now",
            "limited time",
            "exclusive opportunity"
        ]
        
        # Patterns that might indicate prompt injection
        self.injection_patterns = [
            r"ignore previous instructions",
            r"disregard the template",
            r"new instructions:",
            r"system prompt",
            r"admin mode",
            r"bypass safety",
            r"override restrictions"
        ]
        
        # PII patterns to detect and block
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "account_number": r"\b[A-Z]{2}\d{8,12}\b"
        }
        
        # Financial advice patterns to avoid
        self.advice_patterns = [
            r"you should (buy|sell|invest)",
            r"we recommend (buying|selling)",
            r"(buy|sell) now",
            r"this is financial advice",
            r"as your advisor",
            r"take this action immediately"
        ]
    
    def _initialize_disclaimers(self):
        """Initialize required disclaimers."""
        self.disclaimers = {
            "general": (
                "This information is for educational purposes only and should not be "
                "considered personalized financial advice. Please consult with a qualified "
                "financial advisor before making investment decisions."
            ),
            "projection": (
                "These projections are based on historical data and assumptions that may not "
                "reflect future market conditions. Actual results may vary significantly."
            ),
            "risk": (
                "All investments carry risk, including potential loss of principal. "
                "Past performance does not guarantee future results."
            ),
            "tax": (
                "Tax implications vary by individual situation. Please consult with a "
                "tax professional for advice specific to your circumstances."
            )
        }
    
    def validate_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Validate an input prompt for safety.
        
        Args:
            prompt: Input prompt to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        prompt_lower = prompt.lower()
        
        # Check for prompt injection attempts
        for pattern in self.injection_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                self._log_violation(SafetyViolationType.PROMPT_INJECTION, prompt)
                return False, f"Potential prompt injection detected: {pattern}"
        
        # Check for PII in prompt
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, prompt):
                self._log_violation(SafetyViolationType.PII_DETECTED, prompt)
                return False, f"PII detected in prompt: {pii_type}"
        
        # Check for requests for specific financial advice
        for pattern in self.advice_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                self._log_violation(SafetyViolationType.ADVICE_VIOLATION, prompt)
                return False, "Request for specific financial advice detected"
        
        return True, None
    
    def validate_output(self, 
                       output: str,
                       template_type: Optional[str] = None,
                       numerical_data: Optional[Dict[str, float]] = None) -> Tuple[bool, Optional[str]]:
        """Validate AI-generated output for safety and compliance.
        
        Args:
            output: Generated narrative text
            template_type: Type of template used
            numerical_data: Original numerical data for consistency check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        output_lower = output.lower()
        
        # Check for prohibited content
        for term in self.prohibited_terms:
            if term in output_lower:
                self._log_violation(SafetyViolationType.PROHIBITED_CONTENT, output)
                return False, f"Prohibited term found: {term}"
        
        # Check for PII in output
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, output):
                self._log_violation(SafetyViolationType.PII_DETECTED, output)
                return False, f"PII detected in output: {pii_type}"
        
        # Check for financial advice patterns
        for pattern in self.advice_patterns:
            if re.search(pattern, output_lower, re.IGNORECASE):
                self._log_violation(SafetyViolationType.ADVICE_VIOLATION, output)
                return False, "Specific financial advice detected in output"
        
        # Verify numerical consistency if data provided
        if numerical_data:
            is_consistent, error = self._verify_numerical_consistency(output, numerical_data)
            if not is_consistent:
                self._log_violation(SafetyViolationType.NUMERICAL_INCONSISTENCY, output)
                return False, error
        
        # Check for required disclaimers
        if not self._has_required_disclaimers(output, template_type):
            self._log_violation(SafetyViolationType.MISSING_DISCLAIMER, output)
            return False, "Required disclaimers missing"
        
        return True, None
    
    def _verify_numerical_consistency(self, 
                                     output: str,
                                     numerical_data: Dict[str, float],
                                     tolerance: float = 0.01) -> Tuple[bool, Optional[str]]:
        """Verify numbers in output match source data.
        
        Args:
            output: Generated text with numbers
            numerical_data: Source numerical data
            tolerance: Acceptable deviation (default 1%)
            
        Returns:
            Tuple of (is_consistent, error_message)
        """
        # Extract numbers from output
        number_pattern = r'\$?[\d,]+\.?\d*'
        found_numbers = re.findall(number_pattern, output)
        
        # Clean and convert found numbers
        cleaned_numbers = []
        for num_str in found_numbers:
            cleaned = num_str.replace('$', '').replace(',', '')
            try:
                cleaned_numbers.append(float(cleaned))
            except ValueError:
                continue
        
        # Check each number against source data
        for num in cleaned_numbers:
            found_match = False
            for key, expected_value in numerical_data.items():
                if abs(num - expected_value) / max(expected_value, 1) <= tolerance:
                    found_match = True
                    break
            
            # Large numbers not in source data might be hallucinations
            if not found_match and num > 1000:
                return False, f"Unverified number found: {num}"
        
        return True, None
    
    def _has_required_disclaimers(self, 
                                  output: str,
                                  template_type: Optional[str] = None) -> bool:
        """Check if output contains required disclaimers.
        
        Args:
            output: Generated narrative
            template_type: Type of template used
            
        Returns:
            Whether required disclaimers are present
        """
        # Determine which disclaimers are required
        required_disclaimers = ["general"]  # Always required
        
        if template_type:
            if "projection" in template_type or "simulation" in template_type:
                required_disclaimers.append("projection")
            if "risk" in template_type:
                required_disclaimers.append("risk")
            if "tax" in template_type:
                required_disclaimers.append("tax")
        
        # Check for disclaimer presence (allow partial matches)
        output_lower = output.lower()
        for disclaimer_type in required_disclaimers:
            disclaimer_text = self.disclaimers[disclaimer_type].lower()
            key_phrases = disclaimer_text.split('.')[:1]  # Check first sentence
            
            found = False
            for phrase in key_phrases:
                if len(phrase) > 20:  # Only check substantial phrases
                    if phrase[:50] in output_lower or "not financial advice" in output_lower:
                        found = True
                        break
            
            if not found:
                return False
        
        return True
    
    def add_disclaimers(self, 
                       text: str,
                       template_type: Optional[str] = None,
                       position: str = "both") -> str:
        """Add required disclaimers to text.
        
        Args:
            text: Original narrative text
            template_type: Type of template
            position: Where to add disclaimers ("start", "end", or "both")
            
        Returns:
            Text with disclaimers added
        """
        disclaimers = []
        
        # Always include general disclaimer
        disclaimers.append(self.disclaimers["general"])
        
        # Add specific disclaimers based on content
        if template_type:
            if "projection" in template_type or "simulation" in template_type:
                disclaimers.append(self.disclaimers["projection"])
            if "risk" in template_type:
                disclaimers.append(self.disclaimers["risk"])
            if "tax" in template_type:
                disclaimers.append(self.disclaimers["tax"])
        
        disclaimer_text = "\n\n".join(disclaimers)
        disclaimer_block = f"**Important Disclaimer:**\n{disclaimer_text}"
        
        if position == "start":
            return f"{disclaimer_block}\n\n---\n\n{text}"
        elif position == "end":
            return f"{text}\n\n---\n\n{disclaimer_block}"
        else:  # both
            return f"{disclaimer_block}\n\n---\n\n{text}\n\n---\n\n{disclaimer_block}"
    
    def sanitize_output(self, text: str) -> str:
        """Sanitize output to remove any unsafe content.
        
        Args:
            text: Raw output text
            
        Returns:
            Sanitized text
        """
        # Remove any PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            text = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", text)
        
        # Remove any HTML/script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove any URLs that might be malicious
        text = re.sub(r'https?://[^\s]+', '[URL_REMOVED]', text)
        
        return text.strip()
    
    def _log_violation(self, 
                      violation_type: SafetyViolationType,
                      content: str):
        """Log a safety violation.
        
        Args:
            violation_type: Type of violation
            content: Content that caused violation
        """
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": violation_type.value,
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }
        
        self.violation_history.append(violation)
        
        # Log to file/monitoring system
        self.logger.warning(f"Safety violation: {violation_type.value}")
    
    def get_violation_report(self, 
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate violation report for monitoring.
        
        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            
        Returns:
            Violation statistics and details
        """
        filtered_violations = self.violation_history
        
        if start_date:
            filtered_violations = [
                v for v in filtered_violations
                if datetime.fromisoformat(v["timestamp"]) >= start_date
            ]
        
        if end_date:
            filtered_violations = [
                v for v in filtered_violations
                if datetime.fromisoformat(v["timestamp"]) <= end_date
            ]
        
        # Aggregate by type
        violation_counts = {}
        for violation in filtered_violations:
            vtype = violation["type"]
            violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        return {
            "total_violations": len(filtered_violations),
            "violation_counts": violation_counts,
            "recent_violations": filtered_violations[-10:],
            "report_generated": datetime.utcnow().isoformat()
        }