"""
Custom exception classes for BookRAGAgent.

Defines domain-specific exceptions with user-friendly messages.
"""


class RAGError(Exception):
    """Base exception for RAG pipeline errors."""

    def __init__(self, message: str, http_status: int = 500):
        """
        Initialize RAG error.

        Args:
            message: User-friendly error message
            http_status: HTTP status code for API response
        """
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class HallucinationDetectedException(RAGError):
    """Raised when answer is detected to contain hallucinations."""

    def __init__(self, message: str = "The response contains information not supported by the source material."):
        super().__init__(message, http_status=400)


class RetrievalFailedException(RAGError):
    """Raised when chunk retrieval fails."""

    def __init__(self, message: str = "Failed to retrieve relevant information from the knowledge base."):
        super().__init__(message, http_status=503)


class ServiceUnavailableException(RAGError):
    """Raised when external service is unavailable."""

    def __init__(self, service_name: str, message: str = None):
        msg = message or f"The {service_name} service is currently unavailable. Please try again later."
        super().__init__(msg, http_status=503)


class InvalidInputException(RAGError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Invalid input provided."):
        super().__init__(message, http_status=400)


class SessionNotFoundException(RAGError):
    """Raised when session is not found."""

    def __init__(self, session_id: str):
        message = f"Session '{session_id}' not found."
        super().__init__(message, http_status=404)


class ConfigurationException(RAGError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Configuration error."):
        super().__init__(message, http_status=500)


# Error response builders
def build_error_response(error: Exception) -> dict:
    """
    Build standardized error response from exception.

    Args:
        error: Exception instance

    Returns:
        Dictionary with 'error' and 'message' keys
    """
    if isinstance(error, RAGError):
        return {
            "error": error.__class__.__name__,
            "message": error.message
        }
    else:
        return {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }


def get_http_status_code(error: Exception) -> int:
    """
    Get HTTP status code for exception.

    Args:
        error: Exception instance

    Returns:
        HTTP status code (default 500)
    """
    if isinstance(error, RAGError):
        return error.http_status
    return 500
