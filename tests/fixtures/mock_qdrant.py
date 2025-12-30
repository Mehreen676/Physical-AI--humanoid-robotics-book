"""
Mock Qdrant responses for testing.

Provides sample chunks and search results that simulate Qdrant responses.
"""

SAMPLE_CHUNKS = [
    {
        "id": "chunk-001",
        "score": 0.95,
        "payload": {
            "text": "Chapter 1 introduces the fundamental concepts of machine learning, including supervised and unsupervised learning paradigms.",
            "url": "https://example.com/chapter-1",
            "section": "Chapter 1: Introduction to Machine Learning",
            "chunk_id": "chunk-001",
            "position": 1
        }
    },
    {
        "id": "chunk-002",
        "score": 0.88,
        "payload": {
            "text": "Linear regression is a fundamental supervised learning algorithm used for predicting continuous values.",
            "url": "https://example.com/chapter-2",
            "section": "Chapter 2: Linear Regression",
            "chunk_id": "chunk-002",
            "position": 1
        }
    },
    {
        "id": "chunk-042",
        "score": 0.87,
        "payload": {
            "text": "Neural networks consist of interconnected layers of neurons that process information through weighted connections.",
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Neural Networks",
            "chunk_id": "chunk-042",
            "position": 1
        }
    },
    {
        "id": "chunk-043",
        "score": 0.85,
        "payload": {
            "text": "Backpropagation is the fundamental algorithm used to train neural networks by computing gradients.",
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Neural Networks",
            "chunk_id": "chunk-043",
            "position": 2
        }
    },
    {
        "id": "chunk-100",
        "score": 0.82,
        "payload": {
            "text": "Deep learning extends neural networks to multiple layers, enabling learning of complex patterns.",
            "url": "https://example.com/chapter-5",
            "section": "Chapter 5: Deep Learning",
            "chunk_id": "chunk-100",
            "position": 1
        }
    }
]

SAMPLE_HEALTH_RESPONSE = {
    "status": "ok",
    "time": "12.5ms"
}

# Sample search queries and their responses
SEARCH_RESPONSES = {
    "neural networks": SAMPLE_CHUNKS[2:4],  # Chunks 42-43
    "machine learning": SAMPLE_CHUNKS[0:2],  # Chunks 1-2
    "deep learning": SAMPLE_CHUNKS[4:5],  # Chunk 100
}
