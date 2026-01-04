"""Quick verification test for backend_v3."""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=== Backend v3 Verification Test ===\n")

# Test 1: Import Check
print("1. Testing imports...")
try:
    from backend_v3.models import ChatRequest, ChatResponse, Citation
    print("   ✓ Models imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import models: {e}")
    sys.exit(1)

try:
    from backend_v3.api import router
    print("   ✓ API router imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import API router: {e}")
    sys.exit(1)

try:
    from backend_v3.agent import ChatKitAgent, AnswerGenerator
    print("   ✓ Agent components imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import agent: {e}")
    sys.exit(1)

try:
    from backend_v3.storage import get_database
    print("   ✓ Storage layer imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import storage: {e}")
    sys.exit(1)

print()

# Test 2: Configuration Check
print("2. Testing configuration...")
try:
    from backend_v3.config import get_config
    config = get_config()
    print(f"   ✓ Config loaded")
    print(f"   - OpenAI Model: {config.openai_model}")
    print(f"   - API Host: {config.api_host}:{config.api_port}")
    print(f"   - SQLite DB: {config.sqlite_db_path}")
except Exception as e:
    print(f"   ✗ Failed to load config: {e}")
    sys.exit(1)

print()

# Test 3: Database Check
print("3. Testing database...")
try:
    db = get_database()
    session_id = db.create_session(user_id="test_user")
    print(f"   ✓ Created test session: {session_id}")

    # Test adding a turn
    db.add_turn(
        session_id=session_id,
        question="What is ROS 2?",
        retrieval_mode="normal",
        context_chunk_ids=["1", "2", "3"],
        answer="ROS 2 is a robot operating system.",
        grounded=True
    )
    print(f"   ✓ Added conversation turn")

    # Test retrieving history
    history = db.get_conversation_history(session_id)
    print(f"   ✓ Retrieved conversation history ({len(history)} turns)")
except Exception as e:
    print(f"   ✗ Database test failed: {e}")
    sys.exit(1)

print()

# Test 4: Schema Validation
print("4. Testing Pydantic schemas...")
try:
    # Test ChatRequest
    request = ChatRequest(
        session_id="test-123",
        question="What is ROS 2?",
        retrieval_mode="normal"
    )
    print(f"   ✓ ChatRequest validated")

    # Test ChatResponse
    response = ChatResponse(
        session_id="test-123",
        answer="ROS 2 is...",
        citations=[],
        retrieval_mode="normal",
        grounded=True,
        metadata={"latency_ms": 100}
    )
    print(f"   ✓ ChatResponse validated")

    # Test Citation
    citation = Citation(
        chapter="Chapter 1",
        section="Section 1.1",
        text_snippet="ROS 2 is a robot operating system.",
        score=0.95
    )
    print(f"   ✓ Citation validated")
except Exception as e:
    print(f"   ✗ Schema validation failed: {e}")
    sys.exit(1)

print()
print("=" * 50)
print("✓ All backend_v3 verification tests passed!")
print("=" * 50)
print()
print("Backend v3 is ready for use.")
print()
print("To start the server:")
print("  cd backend_v3")
print("  python main.py")
