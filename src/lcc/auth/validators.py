"""Password validation and security utilities."""

import re
from typing import Tuple


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, ""


def is_common_password(password: str) -> bool:
    """
    Check if password is in list of commonly used passwords.
    
    Args:
        password: Password to check
        
    Returns:
        True if password is common, False otherwise
    """
    # Top 20 most common passwords
    common_passwords = {
        "123456", "password", "12345678", "qwerty", "123456789",
        "12345", "1234", "111111", "1234567", "dragon",
        "123123", "baseball", "iloveyou", "trustno1", "1234567890",
        "superman", "1qaz2wsx", "master", "monkey", "letmein",
        "admin", "welcome", "shadow", "ashley", "football",
    }
    
    return password.lower() in common_passwords


def get_password_requirements() -> str:
    """Get human-readable password requirements string."""
    return (
        "Password must be at least 8 characters long and contain:\n"
        "- At least one uppercase letter (A-Z)\n"
        "- At least one lowercase letter (a-z)\n"
        "- At least one digit (0-9)\n"
        "- At least one special character (!@#$%^&*(),.?\":{}|<>)\n"
        "- Must not be a commonly used password"
    )
