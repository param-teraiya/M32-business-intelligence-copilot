"""
Input validation utilities for M32 Business Intelligence System
Provides comprehensive input validation and sanitization.
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, ValidationError, validator
import sqlparse
from sqlparse import sql, tokens

from logger import get_logger

logger = get_logger(__name__)


class SecurityConfig:
    """Security configuration and patterns."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|JOIN)\b.*\b(SELECT)\b)",
        r"(\b(OR|AND)\b.*[=<>].*(\b(OR|AND)\b))",
        r"('[^']*';\s*(DROP|DELETE|INSERT|UPDATE))",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        r"(\b(EXEC|EXECUTE|SP_|XP_)\b)",
        r"(\b(INFORMATION_SCHEMA|SYS\.)\b)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b",
        r"\b(rm|mv|cp|chmod|chown|kill|killall)\b",
        r"\b(wget|curl|nc|telnet|ssh|ftp)\b"
    ]
    
    # Maximum input lengths
    MAX_MESSAGE_LENGTH = 10000
    MAX_SESSION_NAME_LENGTH = 200
    MAX_COMPANY_NAME_LENGTH = 100
    MAX_INDUSTRY_LENGTH = 50


def validate_business_input(input_text: str, input_type: str = "message") -> Dict[str, Any]:
    """
    Validate and sanitize business intelligence input.
    
    Args:
        input_text: Input text to validate
        input_type: Type of input (message, session_name, etc.)
        
    Returns:
        Dictionary with validation results and sanitized input
    """
    if not input_text or not isinstance(input_text, str):
        return {
            "valid": False,
            "error": "Input must be a non-empty string",
            "sanitized": ""
        }
    
    # Check length limits
    max_length = getattr(SecurityConfig, f"MAX_{input_type.upper()}_LENGTH", SecurityConfig.MAX_MESSAGE_LENGTH)
    if len(input_text) > max_length:
        return {
            "valid": False,
            "error": f"Input exceeds maximum length of {max_length} characters",
            "sanitized": input_text[:max_length]
        }
    
    # Check for SQL injection
    sql_check = check_sql_injection(input_text)
    if not sql_check["safe"]:
        logger.warning(f"SQL injection attempt detected: {sql_check['patterns']}")
        return {
            "valid": False,
            "error": "Potentially malicious input detected",
            "sanitized": sanitize_input(input_text),
            "security_issue": "sql_injection"
        }
    
    # Check for XSS
    xss_check = check_xss(input_text)
    if not xss_check["safe"]:
        logger.warning(f"XSS attempt detected: {xss_check['patterns']}")
        return {
            "valid": False,
            "error": "Potentially malicious input detected",
            "sanitized": sanitize_input(input_text),
            "security_issue": "xss"
        }
    
    # Check for command injection
    cmd_check = check_command_injection(input_text)
    if not cmd_check["safe"]:
        logger.warning(f"Command injection attempt detected: {cmd_check['patterns']}")
        return {
            "valid": False,
            "error": "Potentially malicious input detected", 
            "sanitized": sanitize_input(input_text),
            "security_issue": "command_injection"
        }
    
    # Sanitize input
    sanitized = sanitize_input(input_text)
    
    return {
        "valid": True,
        "sanitized": sanitized,
        "original_length": len(input_text),
        "sanitized_length": len(sanitized)
    }


def check_sql_injection(input_text: str) -> Dict[str, Any]:
    """Check for SQL injection patterns."""
    detected_patterns = []
    
    # Convert to lowercase for pattern matching
    text_lower = input_text.lower()
    
    for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected_patterns.append(pattern)
    
    # Additional check using sqlparse
    try:
        parsed = sqlparse.parse(input_text)
        for statement in parsed:
            if statement.get_type() in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']:
                detected_patterns.append(f"SQL statement: {statement.get_type()}")
    except Exception:
        pass  # Not valid SQL, which is fine for business messages
    
    return {
        "safe": len(detected_patterns) == 0,
        "patterns": detected_patterns
    }


def check_xss(input_text: str) -> Dict[str, Any]:
    """Check for XSS patterns."""
    detected_patterns = []
    
    for pattern in SecurityConfig.XSS_PATTERNS:
        if re.search(pattern, input_text, re.IGNORECASE | re.DOTALL):
            detected_patterns.append(pattern)
    
    return {
        "safe": len(detected_patterns) == 0,
        "patterns": detected_patterns
    }


def check_command_injection(input_text: str) -> Dict[str, Any]:
    """Check for command injection patterns."""
    detected_patterns = []
    
    for pattern in SecurityConfig.COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, input_text, re.IGNORECASE):
            detected_patterns.append(pattern)
    
    return {
        "safe": len(detected_patterns) == 0,
        "patterns": detected_patterns
    }


def sanitize_input(input_text: str) -> str:
    """
    Sanitize input by removing/escaping potentially dangerous content.
    
    Args:
        input_text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not input_text:
        return ""
    
    # HTML escape
    sanitized = html.escape(input_text)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Remove or escape dangerous characters for SQL
    # Note: We use parameterized queries, but this is defense in depth
    sanitized = sanitized.replace("'", "''")  # Escape single quotes
    
    # Remove script tags and javascript
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
    
    # Remove event handlers
    sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # Limit consecutive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_session_id(session_id: Union[str, int]) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if isinstance(session_id, int):
        return session_id > 0
    
    if isinstance(session_id, str):
        # Check if it's a numeric string
        if session_id.isdigit():
            return int(session_id) > 0
        
        # Check if it's a valid UUID-like string
        uuid_pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
        return bool(re.match(uuid_pattern, session_id))
    
    return False


def validate_json_input(json_str: str, max_depth: int = 5) -> Dict[str, Any]:
    """
    Validate JSON input with depth and size limits.
    
    Args:
        json_str: JSON string to validate
        max_depth: Maximum nesting depth allowed
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Parse JSON
        data = json.loads(json_str)
        
        # Check depth
        depth = get_json_depth(data)
        if depth > max_depth:
            return {
                "valid": False,
                "error": f"JSON nesting too deep (max {max_depth})",
                "depth": depth
            }
        
        # Check size
        if len(json_str) > 50000:  # 50KB limit
            return {
                "valid": False,
                "error": "JSON too large",
                "size": len(json_str)
            }
        
        return {
            "valid": True,
            "data": data,
            "depth": depth,
            "size": len(json_str)
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {str(e)}"
        }


def get_json_depth(obj: Any, current_depth: int = 0) -> int:
    """Calculate the maximum depth of a JSON object."""
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(get_json_depth(value, current_depth + 1) for value in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(get_json_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth


def validate_business_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate business context information.
    
    Args:
        context: Business context dictionary
        
    Returns:
        Dictionary with validation results
    """
    if not isinstance(context, dict):
        return {
            "valid": False,
            "error": "Business context must be a dictionary"
        }
    
    # Define allowed fields and their validation rules
    allowed_fields = {
        "company": {"max_length": 100, "required": False},
        "industry": {"max_length": 50, "required": False},
        "business_type": {"max_length": 50, "required": False},
        "company_size": {"max_length": 20, "required": False},
        "region": {"max_length": 50, "required": False}
    }
    
    errors = []
    sanitized_context = {}
    
    for field, value in context.items():
        if field not in allowed_fields:
            errors.append(f"Unknown field: {field}")
            continue
        
        if not isinstance(value, str):
            errors.append(f"Field {field} must be a string")
            continue
        
        # Validate length
        max_length = allowed_fields[field]["max_length"]
        if len(value) > max_length:
            errors.append(f"Field {field} exceeds maximum length of {max_length}")
            continue
        
        # Sanitize value
        validation_result = validate_business_input(value, "company_name")
        if not validation_result["valid"]:
            errors.append(f"Field {field}: {validation_result['error']}")
            continue
        
        sanitized_context[field] = validation_result["sanitized"]
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "sanitized_context": sanitized_context
    }


class BusinessInputValidator(BaseModel):
    """Pydantic validator for business inputs."""
    
    message: str
    session_name: Optional[str] = None
    business_context: Optional[Dict[str, Any]] = None
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message content."""
        result = validate_business_input(v, "message")
        if not result["valid"]:
            raise ValueError(result["error"])
        return result["sanitized"]
    
    @validator('session_name')
    def validate_session_name(cls, v):
        """Validate session name."""
        if v is None:
            return v
        
        result = validate_business_input(v, "session_name")
        if not result["valid"]:
            raise ValueError(result["error"])
        return result["sanitized"]
    
    @validator('business_context')
    def validate_business_context(cls, v):
        """Validate business context."""
        if v is None:
            return v
        
        result = validate_business_context(v)
        if not result["valid"]:
            raise ValueError(f"Business context validation failed: {', '.join(result['errors'])}")
        return result["sanitized_context"]


def create_input_validator(input_type: str = "message"):
    """
    Create a validator function for specific input types.
    
    Args:
        input_type: Type of input to validate
        
    Returns:
        Validator function
    """
    def validator(value: str) -> str:
        result = validate_business_input(value, input_type)
        if not result["valid"]:
            raise ValueError(result["error"])
        return result["sanitized"]
    
    return validator
