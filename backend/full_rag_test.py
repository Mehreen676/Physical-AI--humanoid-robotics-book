#!/usr/bin/env python3
"""
Complete RAG Pipeline Test - Tests all components end-to-end
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_all_components():
    """Test all RAG components step by step."""

    print("\n" + "="*70)
    print("COMPLETE RAG PIPELINE TEST")
    print("="*70)

    all_passed = True

    # Test 1: Environment variables
    print("\n[TEST 1] Environment Variables")
    print("-" * 70)
    required_vars = {
        "QDRANT_URL": "Qdrant endpoint",
        "COLLECTION_NAME": "Qdrant collection",
        "OPENROUTER_API_KEY": "OpenRouter API key",
        "COHERE_EMBEDDING_MODEL": "Embedding model",
        "EMBEDDINGS_API_KEY": "Cohere API key"
    }

    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            display = value[:20] + "..." if len(value) > 20 else value
            print(f"  ✓ {var}: {display}")
        else:
            print(f"  ✗ {var}: MISSING ({desc})")
            all_passed = False

    # Test 2: Qdrant Connection
    print("\n[TEST 2] Qdrant Connection")
    print("-" * 70)
    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("COLLECTION_NAME")

        client = QdrantClient(url=qdrant_url, api_key=qdrant_key or None)
        info = client.get_collections()

        print(f"  ✓ Connected to Qdrant at {qdrant_url}")
        print(f"  ✓ Collections found: {len(info.collections)}")

        # Check if collection exists
        collection_exists = any(c.name == collection_name for c in info.collections)
        if collection_exists:
            col_info = client.get_collection(collection_name)
            point_count = col_info.points_count
            print(f"  ✓ Collection '{collection_name}' exists with {point_count} points")

            if point_count == 0:
                print(f"  ⚠ WARNING: Collection is EMPTY - no documents indexed")
                all_passed = False
        else:
            print(f"  ✗ Collection '{collection_name}' NOT found")
            print(f"    Available: {[c.name for c in info.collections]}")
            all_passed = False

    except Exception as e:
        print(f"  ✗ Qdrant connection failed: {e}")
        all_passed = False

    # Test 3: Cohere Embeddings
    print("\n[TEST 3] Cohere Embeddings API")
    print("-" * 70)
    try:
        import cohere
        api_key = os.getenv("EMBEDDINGS_API_KEY")
        model_name = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-light-v3.0")

        co = cohere.ClientV2(api_key=api_key)

        # Test embedding generation
        test_text = "test embedding"
        response = co.embed(
            model=model_name,
            input_type="search_query",
            texts=[test_text]
        )

        embedding_dim = len(response.embeddings[0]) if response.embeddings else 0
        print(f"  ✓ Connected to Cohere API")
        print(f"  ✓ Model: {model_name}")
        print(f"  ✓ Embedding dimension: {embedding_dim}")

    except Exception as e:
        print(f"  ✗ Cohere embeddings failed: {e}")
        all_passed = False

    # Test 4: OpenRouter LLM
    print("\n[TEST 4] OpenRouter LLM API")
    print("-" * 70)
    try:
        import requests

        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("MODEL_NAME", "mistralai/mistral-7b-instruct:free")
        openrouter_url = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1")

        # Test with a simple request
        response = requests.post(
            f"{openrouter_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "Say 'test' only"}
                ],
                "max_tokens": 10,
            },
            timeout=10
        )

        if response.status_code == 200:
            print(f"  ✓ Connected to OpenRouter API")
            print(f"  ✓ Model: {model}")
            print(f"  ✓ API call successful")
        else:
            print(f"  ✗ OpenRouter API error: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            all_passed = False

    except Exception as e:
        print(f"  ✗ OpenRouter LLM failed: {e}")
        all_passed = False

    # Test 5: Retrieval Pipeline
    print("\n[TEST 5] Retrieval Pipeline")
    print("-" * 70)
    try:
        from rag.retrieval import VectorSearchSkill

        retriever = VectorSearchSkill()

        # Test with a simple query
        test_query = "what is RAG?"
        results = retriever.search(query=test_query, top_k=5, threshold=0.3)

        print(f"  ✓ Retrieval pipeline initialized")
        print(f"  ✓ Test query: '{test_query}'")
        print(f"  ✓ Retrieved {len(results)} chunks (threshold=0.3)")

        if len(results) == 0:
            print(f"  ⚠ WARNING: No chunks retrieved")
            print(f"    → Collection may be empty")
            print(f"    → Or similarity threshold may be too high")
            all_passed = False
        else:
            for i, chunk in enumerate(results[:3], 1):
                score = chunk.get("similarity_score", "N/A")
                print(f"    Chunk {i}: score={score}")

    except Exception as e:
        print(f"  ✗ Retrieval pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 6: Full RAG Agent
    print("\n[TEST 6] Full RAG Agent")
    print("-" * 70)
    try:
        from agent.agent import BookRAGAgent

        agent = BookRAGAgent()

        # Test with actual query
        test_query = "what is RAG?"
        response = agent.run(user_query=test_query, session_id="test-session")

        print(f"  ✓ RAG Agent initialized")
        print(f"  ✓ Test query: '{test_query}'")
        print(f"\n  Response:")
        print(f"    Answer: {response.get('answer', 'N/A')[:100]}...")
        print(f"    Retrieved chunks: {len(response.get('retrieved_chunks', []))}")
        print(f"    Citations: {len(response.get('citations', []))}")
        print(f"    Status: {response.get('status', 'unknown')}")

    except Exception as e:
        print(f"  ✗ RAG Agent failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - RAG Pipeline is ready!")
    else:
        print("✗ SOME TESTS FAILED - See details above")
    print("="*70)

    return all_passed

if __name__ == "__main__":
    try:
        success = test_all_components()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
