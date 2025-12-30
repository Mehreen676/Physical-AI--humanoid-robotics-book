"""
Input validation utilities for BookRAGAgent.

Provides validation functions for questions, session IDs, and user input.
"""

import re
import logging
from uuid import UUID
from typing import Optional

logger = logging.getLogger(__name__)


def validate_question(text: str, max_length: int = 500) -> str:
    """
    Validate a user question.

    Args:
        text: Question text
        max_length: Maximum question length

    Returns:
        Validated and sanitized question

    Raises:
        ValueError: If validation fails
    """
    if not text:
        raise ValueError("Question cannot be empty")

    if not isinstance(text, str):
        raise ValueError("Question must be a string")

    # Remove leading/trailing whitespace
    text = text.strip()

    if len(text) == 0:
        raise ValueError("Question cannot be empty or whitespace only")

    if len(text) > max_length:
        raise ValueError(f"Question exceeds maximum length of {max_length} characters")

    # Check for valid characters (allow alphanumeric, punctuation, spaces)
    if not re.match(r"^[\w\s\.,!?:;'\"-()]+$", text, re.UNICODE):
        logger.warning(f"Question contains unusual characters: {text}")

    return text


def validate_session_id(session_id: str) -> str:
    """
    Validate a session ID.

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session ID

    Raises:
        ValueError: If validation fails
    """
    if not session_id:
        raise ValueError("Session ID cannot be empty")

    if not isinstance(session_id, str):
        raise ValueError("Session ID must be a string")

    try:
        # Try to parse as UUID
        UUID(session_id)
        return session_id
    except ValueError:
        raise ValueError(f"Invalid session ID format: {session_id}")


def validate_selected_text(text: str, max_length: int = 5000) -> str:
    """
    Validate selected text restriction.

    Args:
        text: Selected text
        max_length: Maximum text length

    Returns:
        Validated selected text

    Raises:
        ValueError: If validation fails
    """
    if not text:
        raise ValueError("Selected text cannot be empty")

    if not isinstance(text, str):
        raise ValueError("Selected text must be a string")

    text = text.strip()

    if len(text) == 0:
        raise ValueError("Selected text cannot be empty or whitespace only")

    if len(text) > max_length:
        raise ValueError(f"Selected text exceeds maximum length of {max_length} characters")

    return text


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful content.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t\r")

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def validate_role(role: str) -> str:
    """
    Validate message role.

    Args:
        role: Message role

    Returns:
        Validated role

    Raises:
        ValueError: If validation fails
    """
    valid_roles = {"user", "assistant"}

    if not role or role not in valid_roles:
        raise ValueError(f"Role must be one of {valid_roles}")

    return role


def validate_similarity_threshold(threshold: float) -> float:
    """
    Validate similarity threshold.

    Args:
        threshold: Similarity threshold value

    Returns:
        Validated threshold

    Raises:
        ValueError: If validation fails
    """
    try:
        threshold = float(threshold)
    except (ValueError, TypeError):
        raise ValueError("Similarity threshold must be a number")

    if not (0 <= threshold <= 1):
        raise ValueError("Similarity threshold must be between 0 and 1")

    return threshold


def validate_top_k(top_k: int) -> int:
    """
    Validate top_k parameter for retrieval.

    Args:
        top_k: Number of results to return

    Returns:
        Validated top_k

    Raises:
        ValueError: If validation fails
    """
    try:
        top_k = int(top_k)
    except (ValueError, TypeError):
        raise ValueError("top_k must be an integer")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if top_k > 100:
        raise ValueError("top_k cannot exceed 100")

    return top_k
