"""Quick test for semantic retrieval layer."""

import os
from dotenv import load_dotenv
from retrieval import SemanticRetriever, RetrievalConfig

# Load environment variables
load_dotenv()

# Configuration
config = RetrievalConfig(
    qdrant_url=os.getenv("QDRANT_URL"),
    qdrant_api_key=os.getenv("QDRANT_API_KEY"),
    collection_name=os.getenv("COLLECTION_NAME", "data_collection"),
    use_mock_embeddings=True,  # Use mock for testing
    retrieval_top_k=5,
    retrieval_score_threshold=0.7
)

# Initialize retriever
retriever = SemanticRetriever(config)

# Test 1: Health check
print("=== Health Check ===")
health = retriever.health_check()
print(f"Qdrant: {health['qdrant']}")
print(f"Embeddings: {health['embedding_service']}")

# Test 2: Collection info
print("\n=== Collection Info ===")
try:
    info = retriever.get_collection_info()
    print(f"Collection: {info['name']}")
    print(f"Points: {info['points_count']}")
except Exception as e:
    print(f"Skipping collection info (version mismatch): {type(e).__name__}")

# Test 3: Normal retrieval
print("\n=== Normal Retrieval ===")
query = "What is ROS 2?"
results = retriever.retrieve(query=query, retrieval_mode="normal")
print(f"Query: {query}")
print(f"Results: {len(results)}")
for i, chunk in enumerate(results[:3]):
    print(f"\n[{i+1}] Score: {chunk['score']:.3f}")
    print(f"Chapter: {chunk['metadata']['chapter']}")
    print(f"Text: {chunk['text'][:100]}...")

# Test 4: Selected text retrieval
print("\n=== Selected Text Retrieval ===")
selected = "ROS 2 uses DDS for communication between nodes"
results = retriever.retrieve(
    query="How does this work?",
    retrieval_mode="selected_text",
    selected_text=selected
)
print(f"Selected: {selected}")
print(f"Results: {len(results)}")

print("\n=== All Tests Complete ===")
