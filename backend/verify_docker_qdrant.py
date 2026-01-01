#!/usr/bin/env python3
"""
Verify local Docker Qdrant connection and check collection status.
Run this AFTER starting Docker Qdrant: docker start qdrant
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def check_qdrant_docker():
    """Test local Docker Qdrant connection."""
    print("\n" + "="*60)
    print("DOCKER QDRANT VERIFICATION")
    print("="*60)

    # Check .env
    print("\n[STEP 1] Checking .env configuration...")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY", "")
    collection_name = os.getenv("COLLECTION_NAME")

    print(f"  ✓ QDRANT_URL: {qdrant_url}")
    print(f"  ✓ QDRANT_API_KEY: {'(empty - correct for local)' if not qdrant_key else '(SHOULD BE EMPTY for local Docker)'}")
    print(f"  ✓ COLLECTION_NAME: {collection_name}")

    if not qdrant_url or "localhost" not in qdrant_url:
        print("\n  ✗ ERROR: QDRANT_URL must be http://localhost:6333 for local Docker")
        return False

    if qdrant_key and "localhost" in qdrant_url:
        print("\n  ⚠ WARNING: QDRANT_API_KEY should be empty for local Docker")

    # Test connection
    print("\n[STEP 2] Testing Qdrant connection...")
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, api_key=qdrant_key or None)

        # Get server info
        try:
            info = client.get_collections()
            print(f"  ✓ Successfully connected to Qdrant")
            print(f"  ✓ Found {len(info.collections)} collections")

            # Check if our collection exists
            collection_exists = any(c.name == collection_name for c in info.collections)
            if collection_exists:
                print(f"  ✓ Collection '{collection_name}' exists")

                # Get collection stats
                try:
                    collection_info = client.get_collection(collection_name)
                    point_count = collection_info.points_count
                    print(f"  ✓ Points in collection: {point_count}")

                    if point_count == 0:
                        print("\n  ⚠ WARNING: Collection is empty!")
                        print("    → You need to ingest documents first")
                        print("    → Run: python backend/ingest_documents.py")
                    else:
                        print(f"  ✓ Collection has {point_count} documents")
                except Exception as e:
                    print(f"  ✗ Error getting collection info: {e}")
            else:
                print(f"  ✗ Collection '{collection_name}' does NOT exist")
                print(f"    Available collections: {[c.name for c in info.collections]}")
                return False

        except Exception as e:
            print(f"  ✗ Error checking collections: {e}")
            return False

    except Exception as e:
        print(f"  ✗ Failed to connect to Qdrant at {qdrant_url}")
        print(f"    Error: {e}")
        print("\n  Make sure Docker Qdrant is running:")
        print("    docker run -p 6333:6333 qdrant/qdrant:latest")
        print("  or if already created:")
        print("    docker start qdrant")
        return False

    print("\n" + "="*60)
    print("✓ DOCKER QDRANT VERIFICATION PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = check_qdrant_docker()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
