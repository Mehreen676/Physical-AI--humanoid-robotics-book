"""
Sample book chunks for testing.

Contains realistic excerpts from a machine learning textbook that can be used
in unit and integration tests.
"""

CHAPTER_1_CHUNKS = [
    {
        "text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed. It has become increasingly important in applications ranging from natural language processing to computer vision.",
        "metadata": {
            "url": "https://example.com/chapter-1",
            "section": "Chapter 1: What is Machine Learning?",
            "chunk_id": "chunk-001",
            "position": 1,
            "embedding_score": 0.92
        }
    },
    {
        "text": "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models, unsupervised learning discovers patterns in unlabeled data, and reinforcement learning trains agents through reward signals.",
        "metadata": {
            "url": "https://example.com/chapter-1",
            "section": "Chapter 1: Types of Machine Learning",
            "chunk_id": "chunk-002",
            "position": 2,
            "embedding_score": 0.89
        }
    }
]

CHAPTER_3_CHUNKS = [
    {
        "text": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers: input layer, hidden layers, and output layer. Information flows through these layers via weighted connections.",
        "metadata": {
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Neural Networks Fundamentals",
            "chunk_id": "chunk-042",
            "position": 1,
            "embedding_score": 0.87
        }
    },
    {
        "text": "Backpropagation is the fundamental algorithm for training neural networks. It works by computing the gradient of the loss function with respect to each weight in the network, then updating weights in the direction that reduces the loss.",
        "metadata": {
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Training Neural Networks",
            "chunk_id": "chunk-043",
            "position": 2,
            "embedding_score": 0.85
        }
    },
    {
        "text": "Activation functions introduce non-linearity into neural networks, allowing them to learn complex patterns. Common activation functions include ReLU, sigmoid, and tanh. ReLU has become the most popular choice in modern deep learning due to its computational efficiency.",
        "metadata": {
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Activation Functions",
            "chunk_id": "chunk-044",
            "position": 3,
            "embedding_score": 0.83
        }
    }
]

CHAPTER_5_CHUNKS = [
    {
        "text": "Deep learning refers to neural networks with multiple hidden layers. These deep architectures can learn hierarchical representations of data, with earlier layers learning low-level features and deeper layers combining these into higher-level abstractions.",
        "metadata": {
            "url": "https://example.com/chapter-5",
            "section": "Chapter 5: Deep Learning Overview",
            "chunk_id": "chunk-100",
            "position": 1,
            "embedding_score": 0.88
        }
    },
    {
        "text": "Convolutional Neural Networks (CNNs) are specifically designed for processing grid-like data such as images. They use convolutional layers that apply filters to input, pooling layers that downsample, and fully connected layers for classification.",
        "metadata": {
            "url": "https://example.com/chapter-5",
            "section": "Chapter 5: Convolutional Neural Networks",
            "chunk_id": "chunk-101",
            "position": 2,
            "embedding_score": 0.86
        }
    }
]

# Combined sample chunks for retrieval tests
ALL_CHUNKS = CHAPTER_1_CHUNKS + CHAPTER_3_CHUNKS + CHAPTER_5_CHUNKS

# Mapping of keywords to relevant chunks
CHUNK_INDEX = {
    "machine learning": CHAPTER_1_CHUNKS,
    "neural networks": CHAPTER_3_CHUNKS,
    "deep learning": CHAPTER_5_CHUNKS,
    "backpropagation": [CHAPTER_3_CHUNKS[1]],
    "activation functions": [CHAPTER_3_CHUNKS[2]],
    "convolutional": CHAPTER_5_CHUNKS[1:],
}
