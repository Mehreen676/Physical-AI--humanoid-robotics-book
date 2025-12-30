"""
Mock OpenRouter LLM responses for testing.

Provides sample LLM responses that simulate OpenRouter API responses.
"""

SAMPLE_SYNTHESIS_RESPONSE = {
    "id": "chatcmpl-12345",
    "object": "text_completion",
    "created": 1234567890,
    "model": "claude-3-5-sonnet",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Chapter 3 focuses on neural network fundamentals, including the structure of neurons, activation functions, and the backpropagation algorithm used for training. Neural networks are composed of interconnected layers that process information through weighted connections, with backpropagation being the key algorithm for adjusting these weights during training."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 450,
        "completion_tokens": 85,
        "total_tokens": 535
    }
}

SAMPLE_HALLUCINATION_CHECK_RESPONSE = {
    "id": "chatcmpl-12346",
    "object": "text_completion",
    "created": 1234567890,
    "model": "claude-3-5-sonnet",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "GROUNDED"  # Response is grounded in the provided chunks
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 500,
        "completion_tokens": 5,
        "total_tokens": 505
    }
}

SAMPLE_HALLUCINATION_DETECTED_RESPONSE = {
    "id": "chatcmpl-12347",
    "object": "text_completion",
    "created": 1234567890,
    "model": "claude-3-5-sonnet",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "HALLUCINATION: The answer mentions quantum computing, which is not discussed in the provided chunks."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 500,
        "completion_tokens": 20,
        "total_tokens": 520
    }
}

SAMPLE_FALLBACK_RESPONSE = {
    "id": "chatcmpl-12348",
    "object": "text_completion",
    "created": 1234567890,
    "model": "claude-3-5-sonnet",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "I couldn't find information about that topic in the book. Please ask about content covered in the textbook."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "total_tokens": 125
    }
}

# Error responses
TIMEOUT_ERROR = {
    "error": {
        "message": "Request timeout after 30 seconds",
        "type": "timeout_error",
        "code": 504
    }
}

INVALID_API_KEY_ERROR = {
    "error": {
        "message": "Invalid API key provided",
        "type": "authentication_error",
        "code": 401
    }
}
