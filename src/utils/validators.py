"""Input validation utilities for the Agent project.

This module provides validation and sanitization functions for user inputs,
API keys, and messages to ensure data integrity and security.
"""

from __future__ import annotations

import re
from typing import Final

# 상수 정의
API_KEY_MIN_LENGTH: Final[int] = 20
API_KEY_MAX_LENGTH: Final[int] = 200
API_KEY_PATTERN: Final[str] = r"^[a-zA-Z0-9_\-\.]+$"

MESSAGE_DEFAULT_MAX_LENGTH: Final[int] = 4000
MESSAGE_MIN_LENGTH: Final[int] = 1

# 정제할 위험한 문자 패턴
DANGEROUS_PATTERNS: Final[list[str]] = [
    r"<script[^>]*>.*?</script>",  # Script 태그
    r"javascript:",  # JavaScript 프로토콜
    r"on\w+\s*=",  # 이벤트 핸들러
]


def validate_api_key(key: str) -> bool:
    """Validate API key format.

    Checks if the provided API key meets the following criteria:
    - Not empty or whitespace only
    - Length between 20 and 200 characters
    - Contains only alphanumeric characters, underscores, hyphens, and dots
    - Follows a valid pattern (letters, numbers, -, _, .)

    Args:
        key: The API key string to validate.

    Returns:
        bool: True if the API key is valid.

    Raises:
        ValueError: If the API key fails validation with a descriptive message.

    Example:
        >>> validate_api_key("sk-1234567890abcdefghij")
        True

        >>> validate_api_key("invalid key!")
        ValueError: API key contains invalid characters

        >>> validate_api_key("")
        ValueError: API key cannot be empty
    """
    # 빈 문자열 검사
    if not key or not key.strip():
        raise ValueError("API key cannot be empty")

    # 길이 검증
    if len(key) < API_KEY_MIN_LENGTH:
        raise ValueError(
            f"API key is too short (minimum {API_KEY_MIN_LENGTH} characters)"
        )

    if len(key) > API_KEY_MAX_LENGTH:
        raise ValueError(
            f"API key is too long (maximum {API_KEY_MAX_LENGTH} characters)"
        )

    # 패턴 검증 (영문, 숫자, _, -, . 만 허용)
    if not re.match(API_KEY_PATTERN, key):
        raise ValueError(
            "API key contains invalid characters. "
            "Only alphanumeric characters, underscores, hyphens, and dots are allowed"
        )

    # 모든 검증 통과
    return True


def validate_message(message: str, max_length: int = MESSAGE_DEFAULT_MAX_LENGTH) -> bool:
    """Validate user message format and length.

    Checks if the provided message meets the following criteria:
    - Not empty or whitespace only
    - Length does not exceed the maximum allowed
    - Contains printable characters

    Args:
        message: The message string to validate.
        max_length: Maximum allowed length for the message. Defaults to 4000.

    Returns:
        bool: True if the message is valid.

    Raises:
        ValueError: If the message fails validation with a descriptive message.

    Example:
        >>> validate_message("Hello, AI!")
        True

        >>> validate_message("")
        ValueError: Message cannot be empty

        >>> validate_message("x" * 5000)
        ValueError: Message is too long (maximum 4000 characters)

        >>> validate_message("Valid message", max_length=10)
        ValueError: Message is too long (maximum 10 characters)
    """
    # 빈 문자열 검사
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    # 최소 길이 검증 (공백 제거 후)
    stripped_message = message.strip()
    if len(stripped_message) < MESSAGE_MIN_LENGTH:
        raise ValueError("Message must contain at least one character")

    # 최대 길이 검증
    if len(message) > max_length:
        raise ValueError(
            f"Message is too long (maximum {max_length} characters, got {len(message)})"
        )

    # max_length 값 검증
    if max_length < MESSAGE_MIN_LENGTH:
        raise ValueError(
            f"max_length must be at least {MESSAGE_MIN_LENGTH}, got {max_length}"
        )

    # 모든 검증 통과
    return True


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing or escaping dangerous content.

    Removes potentially dangerous patterns such as:
    - HTML script tags
    - JavaScript protocol handlers
    - Event handlers (onclick, onload, etc.)
    - Control characters and null bytes
    - Excessive whitespace

    Args:
        text: The input string to sanitize.

    Returns:
        str: Sanitized version of the input text with dangerous content removed
            and whitespace normalized.

    Example:
        >>> sanitize_input("Hello World")
        'Hello World'

        >>> sanitize_input("<script>alert('xss')</script>Hello")
        'Hello'

        >>> sanitize_input("Click <a onclick='bad()'>here</a>")
        'Click <a >here</a>'

        >>> sanitize_input("  Too   many    spaces  ")
        'Too many spaces'

        >>> sanitize_input("Line1\\nLine2\\n\\nLine3")
        'Line1\\nLine2\\nLine3'
    """
    if not text:
        return ""

    # 1. 위험한 패턴 제거
    sanitized = text
    for pattern in DANGEROUS_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

    # 2. 제어 문자 제거 (줄바꿈, 탭 제외)
    # ASCII 제어 문자 (0-31)를 제거하되 \n(10), \t(9), \r(13)은 유지
    sanitized = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", sanitized)

    # 3. Null 바이트 제거
    sanitized = sanitized.replace("\x00", "")

    # 4. 연속된 공백을 하나로 (줄바꿈은 유지)
    sanitized = re.sub(r" +", " ", sanitized)

    # 5. 연속된 줄바꿈을 최대 2개로 제한
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    # 6. 앞뒤 공백 제거
    sanitized = sanitized.strip()

    return sanitized


def validate_and_sanitize_message(
    message: str, max_length: int = MESSAGE_DEFAULT_MAX_LENGTH
) -> str:
    """Validate and sanitize a message in one step.

    This is a convenience function that combines validation and sanitization.
    First sanitizes the input, then validates the result.

    Args:
        message: The message to validate and sanitize.
        max_length: Maximum allowed length for the message. Defaults to 4000.

    Returns:
        str: Sanitized message that passed validation.

    Raises:
        ValueError: If the message fails validation after sanitization.

    Example:
        >>> validate_and_sanitize_message("  Hello <script>bad</script> World  ")
        'Hello  World'

        >>> validate_and_sanitize_message("")
        ValueError: Message cannot be empty
    """
    # 먼저 정제
    sanitized = sanitize_input(message)

    # 그 다음 검증
    validate_message(sanitized, max_length=max_length)

    return sanitized


def is_valid_api_key(key: str) -> bool:
    """Check if API key is valid without raising an exception.

    This is a non-raising version of validate_api_key() for use in conditional
    statements where you want to check validity without exception handling.

    Args:
        key: The API key string to check.

    Returns:
        bool: True if valid, False otherwise.

    Example:
        >>> is_valid_api_key("sk-1234567890abcdefghij")
        True

        >>> is_valid_api_key("invalid!")
        False

        >>> is_valid_api_key("")
        False
    """
    try:
        return validate_api_key(key)
    except ValueError:
        return False


def is_valid_message(message: str, max_length: int = MESSAGE_DEFAULT_MAX_LENGTH) -> bool:
    """Check if message is valid without raising an exception.

    This is a non-raising version of validate_message() for use in conditional
    statements where you want to check validity without exception handling.

    Args:
        message: The message string to check.
        max_length: Maximum allowed length for the message. Defaults to 4000.

    Returns:
        bool: True if valid, False otherwise.

    Example:
        >>> is_valid_message("Hello!")
        True

        >>> is_valid_message("")
        False

        >>> is_valid_message("x" * 5000)
        False
    """
    try:
        return validate_message(message, max_length=max_length)
    except ValueError:
        return False
