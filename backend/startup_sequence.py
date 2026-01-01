#!/usr/bin/env python3
"""
Startup Sequence: Verify Docker Qdrant + show backend startup command
Run this before starting the backend
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def verify_and_start():
    """Verify Docker Qdrant is running, then show backend startup."""

    print("\n" + "="*70)
    print("BACKEND STARTUP SEQUENCE")
    print("="*70)

    # Step 1: Check .env
    print("\n[STEP 1] Verifying Configuration")
    print("-" * 70)

    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_key = os.getenv("QDRANT_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    collection_name = os.getenv("COLLECTION_NAME", "").strip()

    print(f"QDRANT_URL: {qdrant_url}")
    print(f"QDRANT_API_KEY: {'(empty)' if not qdrant_key else '(set)'}")
    print(f"COLLECTION_NAME: {collection_name}")
    print(f"OPENROUTER_API_KEY: {'(set)' if openrouter_key else '(MISSING - ERROR!)'}")

    if not openrouter_key:
        print("\n✗ OPENROUTER_API_KEY is missing from .env")
        return False

    if not qdrant_url or "localhost" not in qdrant_url:
        print("\n⚠ WARNING: QDRANT_URL should be http://localhost:6333 for local Docker")

    # Step 2: Try to connect to Qdrant
    print("\n[STEP 2] Testing Qdrant Connection")
    print("-" * 70)

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=qdrant_url, api_key=qdrant_key or None)
        info = client.get_collections()

        print(f"✓ Successfully connected to Qdrant")
        print(f"✓ Collections found: {len(info.collections)}")

        collection_exists = any(c.name == collection_name for c in info.collections)
        if collection_exists:
            col_info = client.get_collection(collection_name)
            point_count = col_info.points_count
            print(f"✓ Collection '{collection_name}' exists")
            print(f"✓ Documents indexed: {point_count}")

            if point_count == 0:
                print("\n⚠ WARNING: Collection is EMPTY")
                print("   Documents need to be ingested before RAG will work")
                print("   You can ingest documents by running:")
                print("   → python backend/ingest_documents.py")
        else:
            print(f"\n✗ Collection '{collection_name}' not found")
            return False

    except Exception as e:
        print(f"✗ Failed to connect to Qdrant: {e}")
        print(f"\nMake sure Docker Qdrant is running:")
        print(f"  docker run -p 6333:6333 qdrant/qdrant:latest")
        print(f"  or: docker start qdrant")
        return False

    # Step 3: Show startup command
    print("\n[STEP 3] Backend Ready to Start")
    print("-" * 70)
    print("\n✓ All prerequisites checked!")
    print("\nRun this command to start the FastAPI backend:\n")
    print("  cd backend")
    print("  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("\nOr if using Windows Command Prompt:")
    print("  python -m uvicorn main:app --reload")
    print("\nThe backend will be available at:")
    print("  http://localhost:8000")
    print("  http://localhost:8000/docs (interactive API docs)")
    print("\nTest the RAG pipeline:")
    print("  python backend/full_rag_test.py")

    print("\n" + "="*70)
    return True

if __name__ == "__main__":
    try:
        success = verify_and_start()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
