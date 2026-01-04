"""Error handling utilities."""

import logging
from functools import wraps


class RetrievalError(Exception):
    """Raised when retrieval layer fails."""
    pass


class AgentError(Exception):
    """Raised when agent invocation fails."""
    pass


class DatabaseError(Exception):
    """Raised when database operation fails."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def handle_errors(func):
    """
    Decorator for error handling.

    Logs errors and allows continuation for non-critical failures.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RetrievalError as e:
            logging.error(f"Retrieval error: {str(e)}")
            raise
        except AgentError as e:
            logging.error(f"Agent error: {str(e)}")
            raise
        except DatabaseError as e:
            logging.error(f"Database error: {str(e)}")
            # Don't fail request if only storage fails
            logging.warning("Continuing without persisting turn")
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    return wrapper
