#!/usr/bin/env python3
"""
RAG Retrieval Testing: Query, Search, and Validate Embeddings

Tests the RAG embedding pipeline by executing similarity searches against
Qdrant collection and validating retrieval accuracy and relevance.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

import cohere
from qdrant_client import QdrantClient
from qdrant_client.exceptions import RpcError
from dotenv import load_dotenv


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Set up structured logging for retrieval operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================================
# ENVIRONMENT & CONFIGURATION
# ============================================================================

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book")
COLLECTION_NAME = "rag_embedding"
DEFAULT_K = 5
MAX_RETRIES = 5
INITIAL_WAIT = 1


# ============================================================================
# PHASE 1: CORE RETRIEVAL FUNCTIONS
# ============================================================================

def encode_query(query_text: str) -> List[float]:
    """Convert query text to Cohere embedding vector.

    Args:
        query_text: Text query (3-5000 chars)

    Returns:
        List of 1024 floats (embedding vector)

    Raises:
        ValueError: If query length invalid
        Exception: If Cohere API fails after retries
    """
    if not query_text or len(query_text) < 3:
        raise ValueError(f"Query too short: {len(query_text)} chars (min 3)")
    if len(query_text) > 5000:
        raise ValueError(f"Query too long: {len(query_text)} chars (max 5000)")

    try:
        client = cohere.ClientV2(api_key=COHERE_API_KEY)
        logger.info(f"Encoding query: {query_text[:50]}...")

        retry_count = 0
        wait_time = INITIAL_WAIT

        while retry_count < MAX_RETRIES:
            try:
                response = client.embed(
                    texts=[query_text],
                    model="embed-english-light-v3.0",
                    input_type="default"
                )

                embedding = response.embeddings[0]

                # Validate embedding
                if not isinstance(embedding, list) or len(embedding) != 1024:
                    raise ValueError(f"Invalid embedding dimensions: {len(embedding)}")

                logger.debug(f"Embedding generated: {len(embedding)} dims")
                return embedding

            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    retry_count += 1
                    logger.warning(f"Rate limit hit, retry {retry_count}/{MAX_RETRIES} in {wait_time}s")
                    time.sleep(wait_time)
                    wait_time *= 2
                else:
                    raise

        raise Exception("Max retries exceeded for Cohere API")

    except Exception as e:
        logger.error(f"Error encoding query: {e}")
        raise


def search_qdrant(embedding: List[float], k: int = DEFAULT_K, timeout: int = 10) -> List[dict]:
    """Execute similarity search in Qdrant collection.

    Args:
        embedding: Query embedding vector (1024 dims)
        k: Number of results to return (1-20)
        timeout: Search timeout in seconds

    Returns:
        List of search results with id, score, payload

    Raises:
        ConnectionError: If Qdrant unavailable
        TimeoutError: If search exceeds timeout
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

        logger.info(f"Found {len(results)} results")
        return results

    except RpcError as e:
        logger.error(f"Qdrant connection error: {e}")
        raise ConnectionError(f"Qdrant unavailable: {e}")
    except Exception as e:
        logger.error(f"Error searching Qdrant: {e}")
        if "timeout" in str(e).lower():
            raise TimeoutError(f"Search timeout exceeded: {e}")
        raise


def retrieve_chunks(query_text: str, k: int = DEFAULT_K) -> Dict:
    """Orchestrate complete retrieval pipeline.

    Encodes query → searches Qdrant → formats response

    Args:
        query_text: User query
        k: Top-k results (default 5)

    Returns:
        QueryResponse dict with query, results, metadata
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()

    try:
        # Encode query
        logger.info(f"Retrieving top-{k} chunks for: {query_text[:50]}")
        embedding = encode_query(query_text)

        # Search Qdrant
        search_results = search_qdrant(embedding, k)

        # Format results as RetrievedChunk objects
        results = []
        for rank, result in enumerate(search_results, 1):
            payload = result["payload"]
            results.append({
                "rank": rank,
                "similarity_score": round(result["score"], 4),
                "content": payload.get("content", ""),
                "source_url": payload.get("url", ""),
                "chunk_position": payload.get("position", 0),
                "created_at": payload.get("created_at", ""),
                "chunk_size": payload.get("chunk_size", 0)
            })

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Build QueryResponse
        response = {
            "query": query_text,
            "query_embedding_dimension": 1024,
            "timestamp": timestamp,
            "k": k,
            "results": results,
            "result_count": len(results),
            "execution_time_ms": execution_time_ms,
            "status": "success" if results else "no_results"
        }

        logger.info(f"Retrieval complete: {len(results)} results in {execution_time_ms}ms")
        return response

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "query": query_text,
            "query_embedding_dimension": 1024,
            "timestamp": timestamp,
            "k": k,
            "results": [],
            "result_count": 0,
            "execution_time_ms": execution_time_ms,
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# PHASE 2: RESULT VALIDATION
# ============================================================================

def validate_results(results: List[Dict]) -> Dict:
    """Validate retrieval results for quality and accuracy.

    Args:
        results: List of RetrievedChunk dicts to validate

    Returns:
        Validation report with checks_passed, issues list
    """
    checks_passed = 0
    checks_failed = 0
    issues = []

    # Check 1: Similarity scores in range and sorted
    if results:
        scores = [r["similarity_score"] for r in results]

        for i, score in enumerate(scores):
            if not (0 <= score <= 1):
                issues.append(f"Result {i}: score {score} outside [0,1] range")
                checks_failed += 1
            else:
                checks_passed += 1

        # Check if sorted descending
        if scores != sorted(scores, reverse=True):
            issues.append(f"Results not sorted by score descending")
            checks_failed += 1
        else:
            checks_passed += 1
    else:
        checks_passed += 1  # Empty results OK

    # Check 2: Content not empty
    for i, result in enumerate(results):
        if not result.get("content") or len(result["content"]) < 10:
            issues.append(f"Result {i}: content too short or missing")
            checks_failed += 1
        else:
            checks_passed += 1

    # Check 3: Metadata completeness
    for i, result in enumerate(results):
        metadata_ok = (
            result.get("source_url") and
            isinstance(result.get("chunk_position"), int) and
            result.get("created_at")
        )
        if not metadata_ok:
            issues.append(f"Result {i}: incomplete metadata")
            checks_failed += 1
        else:
            checks_passed += 1

    # Check 4: JSON serializable
    try:
        json.dumps(results)
        checks_passed += 1
    except Exception as e:
        issues.append(f"Results not JSON serializable: {e}")
        checks_failed += 1

    is_valid = checks_failed == 0
    logger.info(f"Validation: {checks_passed} passed, {checks_failed} failed")

    return {
        "is_valid": is_valid,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "issues": issues
    }


# ============================================================================
# PHASE 3: SINGLE QUERY TESTING
# ============================================================================

def run_single_query(query_text: str, k: int = DEFAULT_K, log_file: Optional[str] = None) -> None:
    """Execute and log a single retrieval query.

    Args:
        query_text: Query to execute
        k: Top-k results
        log_file: Optional file path for logging results
    """
    logger.info(f"Running single query: {query_text}")

    # Retrieve chunks
    response = retrieve_chunks(query_text, k)

    # Validate results
    validation = validate_results(response.get("results", []))

    # Add validation to response
    response["validation"] = validation

    # Print to console
    print("\n" + "="*70)
    print("QUERY RESPONSE")
    print("="*70)
    print(json.dumps(response, indent=2))
    print("="*70 + "\n")

    # Log to file if specified
    if log_file:
        try:
            with open(log_file, "a") as f:
                f.write(f"\n{datetime.now().isoformat()} | SINGLE QUERY\n")
                f.write(json.dumps(response, indent=2))
                f.write("\n" + "-"*70 + "\n")
            logger.info(f"Results logged to {log_file}")
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")


# ============================================================================
# PHASE 4: BATCH TESTING
# ============================================================================

def run_batch_test(queries: List[str], k: int = DEFAULT_K, log_file: Optional[str] = None) -> Dict:
    """Execute batch test with multiple queries.

    Args:
        queries: List of query strings (minimum 10)
        k: Top-k results per query
        log_file: Optional file path for logging results

    Returns:
        TestResultLog dict with aggregated statistics
    """
    if len(queries) < 10:
        logger.warning(f"Batch has only {len(queries)} queries (recommended 10+)")

    test_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    start_time = time.time()

    logger.info(f"Starting batch test {test_id} with {len(queries)} queries")

    results = []
    successful_queries = 0
    empty_results_count = 0
    error_count = 0
    scores = []
    times = []

    # Execute each query
    for i, query in enumerate(queries, 1):
        logger.info(f"[{i}/{len(queries)}] {query}")

        response = retrieve_chunks(query, k)
        results.append(response)

        # Collect statistics
        if response["status"] == "success":
            successful_queries += 1
            scores.extend([r["similarity_score"] for r in response["results"]])
            times.append(response["execution_time_ms"])
        elif response["status"] == "no_results":
            empty_results_count += 1
            times.append(response["execution_time_ms"])
        else:
            error_count += 1

    # Calculate statistics
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    min_score = round(min(scores), 4) if scores else 0
    max_score = round(max(scores), 4) if scores else 0
    avg_time = round(sum(times) / len(times), 1) if times else 0

    execution_time_ms = int((time.time() - start_time) * 1000)

    # Build TestResultLog
    test_log = {
        "test_id": test_id,
        "timestamp": timestamp,
        "test_type": "batch",
        "queries_count": len(queries),
        "results": results,
        "statistics": {
            "avg_similarity_score": avg_score,
            "min_similarity_score": min_score,
            "max_similarity_score": max_score,
            "avg_execution_time_ms": avg_time,
            "successful_queries": successful_queries,
            "empty_results_count": empty_results_count,
            "error_count": error_count
        },
        "total_execution_time_ms": execution_time_ms
    }

    # Log to file if specified
    if log_file:
        try:
            with open(log_file, "a") as f:
                f.write(f"\n{timestamp} | BATCH TEST {test_id}\n")
                f.write(json.dumps(test_log, indent=2))
                f.write("\n" + "="*70 + "\n")
            logger.info(f"Batch results logged to {log_file}")
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")

    # Print summary
    print("\n" + "="*70)
    print(f"BATCH TEST SUMMARY: {test_id}")
    print("="*70)
    print(f"Total Queries: {len(queries)}")
    print(f"Successful: {successful_queries}")
    print(f"Empty Results: {empty_results_count}")
    print(f"Errors: {error_count}")
    print(f"Avg Similarity Score: {avg_score}")
    print(f"Score Range: [{min_score}, {max_score}]")
    print(f"Avg Response Time: {avg_time}ms")
    print(f"Total Time: {execution_time_ms}ms")
    print("="*70 + "\n")

    return test_log


# ============================================================================
# MAIN CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG Retrieval Testing")
    parser.add_argument("--query", help="Single query string")
    parser.add_argument("--batch", help="Path to JSON file with query list")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Top-k results")
    parser.add_argument("--log", help="Path to log file for results")

    args = parser.parse_args()

    # Verify configuration
    if not all([COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
        logger.error("Missing required environment variables (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY)")
        sys.exit(1)

    try:
        if args.query:
            # Single query mode
            run_single_query(args.query, args.k, args.log)
        elif args.batch:
            # Batch test mode
            with open(args.batch, "r") as f:
                query_data = json.load(f)

            # Extract queries (support both list of strings and list of dicts)
            if isinstance(query_data, list):
                if isinstance(query_data[0], dict):
                    queries = [q.get("query") for q in query_data]
                else:
                    queries = query_data
            else:
                logger.error("Batch file must contain list of queries")
                sys.exit(1)

            run_batch_test(queries, args.k, args.log)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
