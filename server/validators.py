"""
Input validation utilities
"""
import re
from typing import Tuple


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format
    
    Rules:
    - 3-32 characters
    - Alphanumeric, underscore, hyphen only
    - Must start with alphanumeric
    """
    if not username:
        return False, "Username is required"
    
    # Strip whitespace and normalize
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 32:
        return False, "Username must not exceed 32 characters"
    
    # Check for non-printable or invalid characters
    if not username.isprintable():
        return False, "Username contains invalid or non-printable characters"
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', username):
        # Provide more specific error message showing what was detected
        invalid_chars = set(re.findall(r'[^a-zA-Z0-9_-]', username))
        if invalid_chars:
            return False, f"Username contains invalid characters: {', '.join(repr(c) for c in invalid_chars)}"
        return False, "Username must start with alphanumeric and contain only letters, numbers, underscore, or hyphen"
    
    return True, ""


def validate_password(
    password: str,
    min_length: int = 12,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True
) -> Tuple[bool, str]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    if require_uppercase and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if require_lowercase and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if require_digit and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak patterns
    common_patterns = [
        r'(.)\1{2,}',  # Three or more repeated characters
        r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            return False, "Password contains common patterns that are easily guessed"
    
    return True, ""
