"""
Server-side validation for selected-text mode responses.
Ensures that generated responses are grounded in the selected text.
"""

import logging
import numpy as np
from src.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


def validate_response_in_context(response: str, selected_text: str) -> tuple:
    """
    Validate that response content is grounded in selected text.

    Uses semantic similarity (cosine distance between embeddings) to detect
    whether response concepts are sufficiently based on the selected text.

    Args:
        response: Generated response text
        selected_text: User-selected text (sole context)

    Returns:
        Tuple of (is_valid: bool, confidence_score: float)
        - is_valid: True if confidence >= 0.75 threshold
        - confidence_score: Cosine similarity (0-1)
    """
    try:
        # Get embedding generator
        embeddings = get_embedding_generator()

        # Embed both texts
        response_embedding = np.array(embeddings.embed_text(response))
        context_embedding = np.array(embeddings.embed_text(selected_text))

        # Calculate cosine similarity
        # Cosine similarity = (A · B) / (||A|| × ||B||)
        dot_product = np.dot(response_embedding, context_embedding)
        norm_response = np.linalg.norm(response_embedding)
        norm_context = np.linalg.norm(context_embedding)

        if norm_response == 0 or norm_context == 0:
            # Edge case: empty embedding
            logger.warning("Validation: One of the embeddings is zero")
            return False, 0.0

        similarity = dot_product / (norm_response * norm_context)

        # Threshold: 0.75 (tunable)
        # Responses with high semantic similarity to selected text pass
        confidence_threshold = 0.75
        is_valid = similarity >= confidence_threshold

        # Clamp similarity to [0, 1] range in case of numerical issues
        confidence = float(max(0, min(1, similarity)))

        if not is_valid:
            logger.warning(
                f"⚠️ Response validation failed: "
                f"confidence={confidence:.3f} < threshold={confidence_threshold}"
            )
        else:
            logger.info(
                f"✅ Response validation passed: confidence={confidence:.3f}"
            )

        return is_valid, confidence

    except Exception as e:
        logger.error(f"❌ Validation error: {e}", exc_info=True)
        # On error, fail validation to be conservative
        return False, 0.0
