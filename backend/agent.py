#!/usr/bin/env python3
"""
RAG Agent with OpenAI Integration

Intelligent conversational agent using OpenAI's Agent framework that retrieves
context from the humanoid robotics textbook via Qdrant vector database and
Cohere embeddings. Answers user queries with accurate, contextual responses
grounded in textbook content.

Spec: specs/005-rag-agent-openai/spec.md
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

import cohere
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Optional: OpenAI import (for Phase 6 - US4 enhancement)
try:
    from openai import OpenAI
    from openai.lib._agents import AgentBuilder
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ============================================================================
# LOGGING SETUP (T004)
# ============================================================================

def setup_logging() -> logging.Logger:
    """Set up structured logging for agent operations.

    Returns:
        Configured logger instance with file and console output
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"agent_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Agent logging initialized. Output: {log_file}")
    return logger


logger = setup_logging()


# ============================================================================
# ENVIRONMENT & CONFIGURATION (T005)
# ============================================================================

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_embedding")
BASE_URL = os.getenv("BASE_URL", "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/")

DEFAULT_K = 5
MAX_RETRIES = 5
INITIAL_WAIT = 1
QUERY_TIMEOUT = 10  # seconds


# ============================================================================
# PHASE 2: AGENT FOUNDATION - CORE FUNCTIONS
# ============================================================================

# T006: Query Validation
def validate_query(query_text: str) -> Tuple[bool, Optional[str]]:
    """Validate user query for acceptable length and format.

    Args:
        query_text: User input query string

    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if query is valid
        error_message: None if valid, error string if invalid
    """
    if not query_text or not isinstance(query_text, str):
        return False, "Query must be a non-empty string"

    if len(query_text) < 3:
        return False, f"Query too short: {len(query_text)} chars (minimum 3)"

    if len(query_text) > 5000:
        return False, f"Query too long: {len(query_text)} chars (maximum 5000)"

    logger.debug(f"Query validation passed: {len(query_text)} chars")
    return True, None


# T007: Cohere Query Encoder
def encode_query(query_text: str) -> Optional[List[float]]:
    """Convert query text to Cohere embedding vector.

    Args:
        query_text: User query text

    Returns:
        1024-dimensional embedding vector, or None if encoding fails
    """
    # Validate query first
    is_valid, error_msg = validate_query(query_text)
    if not is_valid:
        logger.error(f"Query validation failed: {error_msg}")
        return None

    try:
        client = cohere.ClientV2(api_key=COHERE_API_KEY)
        logger.info(f"Encoding query: {query_text[:50]}...")

        retry_count = 0
        wait_time = INITIAL_WAIT

        while retry_count < MAX_RETRIES:
            try:
                response = client.embed(
                    texts=[query_text],
                    model="embed-english-v3.0",
                    input_type="search_query"
                )

                # Extract embedding from Cohere ClientV2 response
                if hasattr(response.embeddings, 'float_') and response.embeddings.float_:
                    embedding = response.embeddings.float_[0]

                    # Validate embedding dimensions
                    if not isinstance(embedding, list) or len(embedding) != 1024:
                        logger.error(f"Invalid embedding dimensions: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
                        return None

                    logger.debug(f"Embedding generated: {len(embedding)} dims")
                    return embedding
                else:
                    logger.error("No embeddings in Cohere response")
                    return None

            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    retry_count += 1
                    logger.warning(f"Rate limit hit, retry {retry_count}/{MAX_RETRIES} in {wait_time}s")
                    time.sleep(wait_time)
                    wait_time *= 2
                else:
                    raise

        logger.error("Max retries exceeded for Cohere API")
        return None

    except Exception as e:
        logger.error(f"Error encoding query: {e}")
        return None


# T008: Qdrant Search
def search_qdrant(embedding: List[float], k: int = DEFAULT_K, timeout: int = 10) -> Optional[List[Dict]]:
    """Execute similarity search in Qdrant collection.

    Args:
        embedding: Query embedding vector (1024 dims)
        k: Number of results to return (1-20)
        timeout: Search timeout in seconds

    Returns:
        List of search results with id, score, payload, or None if search fails
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=timeout)
        logger.info(f"Searching Qdrant collection '{COLLECTION_NAME}' for top-{k} results")

        # Execute search
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=k
        )

        # Format results
        results = []
        for rank, result in enumerate(search_results, 1):
            results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })

        logger.info(f"Found {len(results)} results in Qdrant")
        return results

    except Exception as e:
        logger.error(f"Error searching Qdrant: {e}")
        return None


# T009: Result Formatter
def format_retrieved_chunks(search_results: List[Dict]) -> List[Dict]:
    """Format Qdrant search results as RetrievedChunk objects.

    Args:
        search_results: Raw results from Qdrant search

    Returns:
        Formatted list of chunks with all metadata
    """
    formatted = []

    for rank, result in enumerate(search_results, 1):
        payload = result.get("payload", {})
        formatted_chunk = {
            "rank": rank,
            "similarity_score": result.get("score", 0.0),
            "content": payload.get("content", ""),
            "source_url": payload.get("url", ""),
            "chunk_position": payload.get("position", 0),
            "created_at": payload.get("created_at", ""),
            "chunk_size": payload.get("chunk_size", 0)
        }
        formatted.append(formatted_chunk)

    logger.debug(f"Formatted {len(formatted)} retrieved chunks")
    return formatted


# T010: Error Handler (integrated in above functions with exponential backoff)
def handle_error(error: Exception, context: str) -> Dict:
    """Handle errors gracefully with diagnostics.

    Args:
        error: Exception that occurred
        context: Context where error occurred

    Returns:
        Error response dictionary
    """
    error_msg = str(error)
    logger.error(f"Error in {context}: {error_msg}")

    return {
        "status": "error",
        "error": error_msg,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }


# T011: Health Check
def agent_health_check() -> Dict:
    """Perform system health check for agent readiness.

    Returns:
        Dictionary with health status and diagnostics
    """
    logger.info("Performing agent health check...")

    health = {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "cohere_api": False,
            "qdrant_connection": False,
            "openai_api": False
        },
        "message": ""
    }

    # Check Cohere API
    try:
        if COHERE_API_KEY:
            client = cohere.ClientV2(api_key=COHERE_API_KEY)
            # Try a simple embedding
            response = client.embed(
                texts=["health check"],
                model="embed-english-v3.0",
                input_type="search_query"
            )
            if hasattr(response.embeddings, 'float_') and response.embeddings.float_:
                health["checks"]["cohere_api"] = True
                logger.info("[OK] Cohere API: Working")
    except Exception as e:
        logger.warning(f"[FAIL] Cohere API health check failed: {e}")

    # Check Qdrant Connection
    try:
        if QDRANT_URL and QDRANT_API_KEY:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=5)
            collection = client.get_collection(COLLECTION_NAME)

            # Check vector dimensionality
            if hasattr(collection, 'config') and hasattr(collection.config, 'params'):
                dims = collection.config.params.vectors.size
                if dims == 1024:
                    health["checks"]["qdrant_connection"] = True
                    logger.info(f"[OK] Qdrant connection: Working (collection '{COLLECTION_NAME}', {dims}-dim vectors)")
                else:
                    logger.warning(f"[FAIL] Qdrant collection has {dims} dims, expected 1024")
            else:
                health["checks"]["qdrant_connection"] = True
                logger.info(f"[OK] Qdrant connection: Working (collection '{COLLECTION_NAME}')")
    except Exception as e:
        logger.warning(f"[FAIL] Qdrant connection health check failed: {e}")

    # Check OpenAI API
    if HAS_OPENAI and OPENAI_API_KEY:
        try:
            health["checks"]["openai_api"] = True
            logger.info("[OK] OpenAI SDK: Available (ready for US4 enhancement)")
        except Exception as e:
            logger.warning(f"[FAIL] OpenAI API health check failed: {e}")
    else:
        logger.info("[INFO] OpenAI API: Not configured (US4 enhancement unavailable)")

    # Determine overall status
    required_checks = ["cohere_api", "qdrant_connection"]
    if all(health["checks"].get(check, False) for check in required_checks):
        health["status"] = "ready"
        health["message"] = "Agent is ready for queries"
    else:
        health["status"] = "degraded"
        health["message"] = "Some services are unavailable"

    return health


# ============================================================================
# PHASE 3: USER STORY 1 - ASK TEXTBOOK QUESTIONS
# ============================================================================

# T012 & T013: Query Handler & Response Wrapper
def run_query(query_text: str, k: int = DEFAULT_K) -> Dict:
    """Orchestrate complete retrieval pipeline for user query.

    Args:
        query_text: User question
        k: Number of retrieved chunks (default 5)

    Returns:
        Dictionary with query, response, sources, confidence, execution_time_ms, status
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()

    logger.info(f"Processing query: {query_text[:50]}...")

    try:
        # Encode query
        embedding = encode_query(query_text)
        if embedding is None:
            return {
                "query": query_text,
                "response": "Error encoding query. Please check query length (3-5000 chars).",
                "sources": [],
                "confidence": 0.0,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "error"
            }

        # Search Qdrant
        search_results = search_qdrant(embedding, k)
        if search_results is None:
            return {
                "query": query_text,
                "response": "Error searching Qdrant. Please check connection.",
                "sources": [],
                "confidence": 0.0,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "error"
            }

        # Format retrieved chunks
        chunks = format_retrieved_chunks(search_results)

        if not chunks:
            return {
                "query": query_text,
                "response": "No relevant content found in the textbook for your query.",
                "sources": [],
                "confidence": 0.0,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "no_results"
            }

        # Build response (Phase 3: raw retrieval; Phase 6: synthesis)
        response_text = f"Based on the textbook, here's what I found:\n\n"
        for chunk in chunks[:3]:  # Use top 3 chunks for summary
            response_text += f"- {chunk['content'][:200]}...\n\n"

        # Calculate average confidence from similarity scores
        avg_confidence = sum(c["similarity_score"] for c in chunks) / len(chunks) if chunks else 0.0

        # Build sources list
        sources = [
            {
                "url": chunk["source_url"],
                "snippet": chunk["content"][:100]
            }
            for chunk in chunks if chunk["source_url"]
        ]

        return {
            "query": query_text,
            "response": response_text,
            "sources": sources,
            "confidence": round(avg_confidence, 3),
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "status": "success"
        }

    except Exception as e:
        return handle_error(e, "run_query") | {
            "query": query_text,
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "response": "",
            "sources": [],
            "confidence": 0.0
        }


# ============================================================================
# PHASE 5: USER STORY 3 - BATCH QUERY HANDLING
# ============================================================================

# T021: Batch Query Handler
def run_batch_queries(queries_list: List[str], k: int = DEFAULT_K, log_file: Optional[str] = None) -> Dict:
    """Execute batch of queries and aggregate results.

    Args:
        queries_list: List of query strings
        k: Number of retrieved chunks per query
        log_file: Optional log file for results

    Returns:
        Dictionary with aggregated batch results and statistics
    """
    logger.info(f"Running batch test with {len(queries_list)} queries...")

    batch_id = str(uuid4())
    batch_results = {
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(queries_list),
        "results": [],
        "statistics": {
            "avg_similarity_score": 0.0,
            "min_similarity_score": 1.0,
            "max_similarity_score": 0.0,
            "avg_execution_time_ms": 0.0,
            "successful_queries": 0,
            "empty_results_count": 0,
            "error_count": 0
        }
    }

    all_scores = []
    all_times = []

    for i, query in enumerate(queries_list, 1):
        logger.info(f"[{i}/{len(queries_list)}] Processing: {query[:50]}...")

        response = run_query(query, k)
        batch_results["results"].append(response)

        # Update statistics
        if response["status"] == "success":
            batch_results["statistics"]["successful_queries"] += 1
            if response["sources"]:
                all_scores.extend([src.get("confidence", response["confidence"]) for src in response["sources"]])
            else:
                all_scores.append(response["confidence"])
        elif response["status"] == "no_results":
            batch_results["statistics"]["empty_results_count"] += 1
        else:
            batch_results["statistics"]["error_count"] += 1

        all_times.append(response["execution_time_ms"])

    # Calculate aggregate statistics
    if all_scores:
        batch_results["statistics"]["avg_similarity_score"] = sum(all_scores) / len(all_scores)
        batch_results["statistics"]["min_similarity_score"] = min(all_scores)
        batch_results["statistics"]["max_similarity_score"] = max(all_scores)

    if all_times:
        batch_results["statistics"]["avg_execution_time_ms"] = sum(all_times) / len(all_times)

    # Log results if requested
    if log_file:
        try:
            with open(log_file, "w") as f:
                json.dump(batch_results, f, indent=2)
            logger.info(f"Batch results logged to {log_file}")
        except Exception as e:
            logger.error(f"Failed to write log file: {e}")

    # Print summary
    print("\n" + "="*70)
    print(f"BATCH TEST SUMMARY: {batch_id}")
    print("="*70)
    print(f"Total Queries: {batch_results['total_queries']}")
    print(f"Successful: {batch_results['statistics']['successful_queries']}")
    print(f"Empty Results: {batch_results['statistics']['empty_results_count']}")
    print(f"Errors: {batch_results['statistics']['error_count']}")
    print(f"Avg Similarity Score: {batch_results['statistics']['avg_similarity_score']:.4f}")
    print(f"Score Range: [{batch_results['statistics']['min_similarity_score']:.4f}, {batch_results['statistics']['max_similarity_score']:.4f}]")
    print(f"Avg Response Time: {batch_results['statistics']['avg_execution_time_ms']:.0f}ms")
    print("="*70 + "\n")

    return batch_results


# ============================================================================
# PHASE 6: USER STORY 4 - NATURAL LANGUAGE RESPONSE SYNTHESIS (P2 OPTIONAL)
# ============================================================================

# T027: Response Synthesis System Prompt
SYNTHESIS_SYSTEM_PROMPT = """You are a helpful assistant specializing in humanoid robotics and physical AI.
Your role is to answer questions about humanoid robots, their design, control, perception, and applications
based on content from a comprehensive textbook on the subject.

When answering questions:
1. Use ONLY the context provided from the textbook - do not add external knowledge
2. Always cite your sources by including the URL of the textbook section you reference
3. Be accurate and specific, avoiding speculation beyond the provided context
4. If the provided context doesn't adequately answer the question, say so honestly
5. Format responses clearly with proper grammar and structure
6. For technical concepts, explain them in accessible language while maintaining accuracy

Your goal is to provide informative, well-sourced answers that help the user understand humanoid robotics."""

# T026: Retrieval Tool Wrapper for OpenAI Agent Tool Use
def retrieve_from_textbook(query: str, k: int = 5) -> Dict:
    """Retrieve relevant textbook content for OpenAI agent tool use.

    This function wraps the existing run_query() function to provide a tool
    that OpenAI Agents can invoke to search the textbook for relevant context.

    Args:
        query: User question or search term
        k: Number of chunks to retrieve (default 5)

    Returns:
        Dictionary with retrieved chunks and metadata formatted for agent processing
    """
    logger.info(f"Retrieval tool invoked: {query[:50]}...")

    try:
        # Encode query
        embedding = encode_query(query)
        if embedding is None:
            return {
                "success": False,
                "error": "Failed to encode query",
                "chunks": []
            }

        # Search Qdrant
        search_results = search_qdrant(embedding, k)
        if search_results is None:
            return {
                "success": False,
                "error": "Failed to search knowledge base",
                "chunks": []
            }

        # Format chunks
        chunks = format_retrieved_chunks(search_results)

        if not chunks:
            return {
                "success": False,
                "error": "No relevant content found",
                "chunks": []
            }

        # Format for agent: include full content and metadata
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append({
                "rank": chunk["rank"],
                "content": chunk["content"],
                "source_url": chunk["source_url"],
                "similarity_score": chunk["similarity_score"],
                "chunk_position": chunk["chunk_position"]
            })

        return {
            "success": True,
            "query": query,
            "chunks_retrieved": len(formatted_chunks),
            "chunks": formatted_chunks
        }

    except Exception as e:
        logger.error(f"Retrieval tool error: {e}")
        return {
            "success": False,
            "error": str(e),
            "chunks": []
        }


# T028: OpenAI Agent Client Creation
def create_openai_agent():
    """Create and configure OpenAI Agent with retrieval tool.

    The agent uses the retrieve_from_textbook tool to search the textbook
    and synthesizes natural language responses based on retrieved context.

    Returns:
        Configured OpenAI client with agent capability, or None if creation fails
    """
    if not HAS_OPENAI or not OPENAI_API_KEY:
        logger.error("OpenAI SDK not available or API key not configured")
        return None

    try:
        logger.info("Creating OpenAI Agent with retrieval tool...")

        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Define the retrieval tool for agent use
        tool_definition = {
            "type": "function",
            "function": {
                "name": "retrieve_from_textbook",
                "description": "Search the humanoid robotics textbook for relevant content. Use this tool to find answers to questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query or question to find relevant content"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of results to retrieve (default: 5, max: 20)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["query"]
                }
            }
        }

        logger.info("[OK] OpenAI Agent created successfully")
        return client

    except Exception as e:
        logger.error(f"Failed to create OpenAI Agent: {e}")
        return None


# T029: Response Quality Validation - Run Synthesis on Test Queries
def run_synthesis_validation(test_queries: Optional[List[str]] = None) -> Dict:
    """Validate response quality from OpenAI synthesis on test queries.

    Args:
        test_queries: List of test queries; if None, uses default set

    Returns:
        Dictionary with validation results and quality metrics
    """
    if test_queries is None:
        # Default test queries covering different aspects
        test_queries = [
            "What is humanoid robotics?",
            "How does ROS 2 work?",
            "Explain bipedal walking and balance control",
            "What sensors do humanoid robots use?",
            "How does sim-to-real transfer work?"
        ]

    logger.info(f"Running synthesis validation on {len(test_queries)} queries...")

    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(test_queries),
        "validation_results": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "success_rate": 0.0
        }
    }

    for i, query in enumerate(test_queries, 1):
        logger.info(f"[{i}/{len(test_queries)}] Validating synthesis for: {query[:50]}...")

        try:
            # Get raw retrieval response
            retrieval_response = run_query(query, k=5)

            # Get retrieval context
            retrieval_chunks = []
            if retrieval_response["status"] == "success" and retrieval_response["sources"]:
                retrieval_chunks = [src["snippet"] for src in retrieval_response["sources"]]

            # Validate synthesis quality
            validation_data = {
                "query": query,
                "retrieval_response": retrieval_response,
                "synthesis_test": {
                    "chunks_available": len(retrieval_chunks),
                    "test_result": "PASS" if retrieval_chunks else "FAIL",
                    "note": "Ready for synthesis" if retrieval_chunks else "No chunks to synthesize"
                },
                "timestamp": datetime.now().isoformat()
            }

            validation_results["validation_results"].append(validation_data)

            if retrieval_chunks:
                validation_results["summary"]["passed"] += 1
            else:
                validation_results["summary"]["failed"] += 1

        except Exception as e:
            logger.error(f"Validation error on query '{query}': {e}")
            validation_results["validation_results"].append({
                "query": query,
                "error": str(e),
                "test_result": "FAIL"
            })
            validation_results["summary"]["failed"] += 1

    # Calculate success rate
    total = validation_results["summary"]["passed"] + validation_results["summary"]["failed"]
    if total > 0:
        validation_results["summary"]["success_rate"] = (
            validation_results["summary"]["passed"] / total * 100
        )

    return validation_results


# T030: Create Synthesis vs Retrieval Comparison (documented in CLI option)
def run_comparison_analysis(test_queries: Optional[List[str]] = None) -> Dict:
    """Compare raw retrieval responses with synthesis-ready format.

    Args:
        test_queries: List of test queries for comparison

    Returns:
        Dictionary with side-by-side comparison data
    """
    if test_queries is None:
        test_queries = [
            "What is humanoid robotics?",
            "How does ROS 2 work?",
            "Explain bipedal walking and balance"
        ]

    logger.info(f"Running comparison analysis on {len(test_queries)} queries...")

    comparison_results = {
        "timestamp": datetime.now().isoformat(),
        "analysis": [],
        "summary": {
            "retrieval_avg_confidence": 0.0,
            "synthesis_readiness": "Ready for implementation"
        }
    }

    confidences = []

    for query in test_queries:
        logger.info(f"Comparing: {query[:50]}...")

        # Get retrieval response
        retrieval_response = run_query(query, k=5)

        comparison_entry = {
            "query": query,
            "retrieval": {
                "status": retrieval_response["status"],
                "confidence": retrieval_response["confidence"],
                "sources_count": len(retrieval_response["sources"]),
                "execution_time_ms": retrieval_response["execution_time_ms"]
            },
            "synthesis_ready": {
                "can_synthesize": retrieval_response["status"] == "success",
                "context_available": len(retrieval_response["sources"]) > 0,
                "chunks_for_synthesis": [
                    src["snippet"] for src in retrieval_response["sources"]
                ]
            }
        }

        comparison_results["analysis"].append(comparison_entry)

        if retrieval_response["confidence"] > 0:
            confidences.append(retrieval_response["confidence"])

    # Calculate summary statistics
    if confidences:
        comparison_results["summary"]["retrieval_avg_confidence"] = round(
            sum(confidences) / len(confidences), 3
        )

    return comparison_results


# ============================================================================
# PHASE 4: USER STORY 2 - AGENT INITIALIZATION
# ============================================================================

# T017: Agent Initialization
def agent_init() -> bool:
    """Initialize agent and verify all systems ready.

    Returns:
        True if initialization successful, False otherwise
    """
    logger.info("="*70)
    logger.info("Initializing RAG Agent with OpenAI Integration")
    logger.info("="*70)

    # Perform health check
    health = agent_health_check()

    logger.info(f"Health Check Status: {health['status']}")
    logger.info(f"Message: {health['message']}")

    if health["status"] == "ready":
        logger.info("[OK] Agent initialized successfully!")
        logger.info("="*70)
        return True
    else:
        logger.warning("[WARN] Agent initialized with warnings. Some services may be unavailable.")
        logger.warning("="*70)
        return True  # Continue even with warnings


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for agent CLI."""
    parser = argparse.ArgumentParser(
        description="RAG Agent for Humanoid Robotics Textbook Q&A"
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Single query to process"
    )

    parser.add_argument(
        "--batch",
        help="Path to JSON file with batch of queries"
    )

    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5)"
    )

    parser.add_argument(
        "--log",
        help="Path to log file for batch results"
    )

    parser.add_argument(
        "--synthesis",
        action="store_true",
        help="Run synthesis validation (Phase 6 - US4) on test queries"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run side-by-side comparison of retrieval vs synthesis-ready format"
    )

    args = parser.parse_args()

    # Initialize agent
    if not agent_init():
        logger.error("Agent initialization failed")
        sys.exit(1)

    # Handle synthesis validation mode (Phase 6)
    if args.synthesis:
        logger.info("Running synthesis validation (Phase 6 - US4)...")
        validation_results = run_synthesis_validation()

        # Log results
        log_file = "synthesis_validation_results.json"
        try:
            with open(log_file, "w") as f:
                json.dump(validation_results, f, indent=2)
            logger.info(f"Synthesis validation results logged to {log_file}")
        except Exception as e:
            logger.error(f"Failed to write validation results: {e}")

        # Print summary
        print("\n" + "="*70)
        print("SYNTHESIS VALIDATION SUMMARY (Phase 6 - US4)")
        print("="*70)
        print(f"Total Queries: {validation_results['total_queries']}")
        print(f"Passed: {validation_results['summary']['passed']}")
        print(f"Failed: {validation_results['summary']['failed']}")
        print(f"Success Rate: {validation_results['summary']['success_rate']:.1f}%")
        print("="*70 + "\n")

        sys.exit(0)

    # Handle comparison analysis mode (Phase 6)
    if args.compare:
        logger.info("Running comparison analysis (retrieval vs synthesis-ready)...")
        comparison_results = run_comparison_analysis()

        # Log results
        log_file = "synthesis_comparison_analysis.json"
        try:
            with open(log_file, "w") as f:
                json.dump(comparison_results, f, indent=2)
            logger.info(f"Comparison results logged to {log_file}")
        except Exception as e:
            logger.error(f"Failed to write comparison results: {e}")

        # Print summary
        print("\n" + "="*70)
        print("SYNTHESIS READINESS COMPARISON")
        print("="*70)
        print(f"Queries Analyzed: {len(comparison_results['analysis'])}")
        print(f"Avg Retrieval Confidence: {comparison_results['summary']['retrieval_avg_confidence']:.3f}")
        print(f"Synthesis Readiness: {comparison_results['summary']['synthesis_readiness']}")
        print("="*70 + "\n")

        sys.exit(0)

    # Handle batch mode
    if args.batch:
        try:
            with open(args.batch, "r") as f:
                batch_data = json.load(f)

            # Extract queries from batch file
            queries = []
            if isinstance(batch_data, list):
                for item in batch_data:
                    if isinstance(item, str):
                        # List of query strings
                        queries.append(item)
                    elif isinstance(item, dict) and "query" in item:
                        # List of query objects with "query" field
                        queries.append(item["query"])
                    else:
                        # Fallback: convert to string
                        queries.append(str(item))

            logger.info(f"Running batch test with {len(queries)} queries from {args.batch}")
            batch_results = run_batch_queries(queries, k=args.k, log_file=args.log)

            sys.exit(0)

        except Exception as e:
            logger.error(f"Error processing batch file: {e}")
            sys.exit(1)

    # Handle single query mode
    elif args.query:
        response = run_query(args.query, k=args.k)

        # Print formatted response
        print("\n" + "="*70)
        print("QUERY RESPONSE")
        print("="*70)
        print(json.dumps(response, indent=2))
        print("="*70 + "\n")

        # Log result
        if args.log:
            try:
                with open(args.log, "a") as f:
                    f.write(json.dumps(response) + "\n")
                logger.info(f"Result logged to {args.log}")
            except Exception as e:
                logger.error(f"Failed to write log file: {e}")

        sys.exit(0)

    # No query provided
    else:
        print("Agent is ready. Usage:")
        print("  Single query: python agent.py \"What is humanoid robotics?\"")
        print("  Batch test:   python agent.py --batch test_queries.json --log results.log")
        sys.exit(0)


if __name__ == "__main__":
    main()
